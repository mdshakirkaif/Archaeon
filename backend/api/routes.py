from __future__ import annotations

import sys
import threading
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

# ---------------------------------------------------------------------------
# Path patches so we can import from sibling directories
# ---------------------------------------------------------------------------
_backend = Path(__file__).resolve().parent.parent  # backend/
sys.path.append(str(_backend / "ai-langgraph-agent"))
sys.path.append(str(_backend / "rag"))

from github_analyzer import analyze_github          # ai-langgraph-agent
from interview_agent import interview_agent         # ai-langgraph-agent
from retriever import retrieve_relevant_context     # rag
from generator import generate_grounded_answer      # rag

from database import get_db, SessionLocal
from models import (
    Session as SessionModel,
    SessionResponse,
    CreateSessionRequest,
    ChatResponse,
    AskResponse,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory session state store
# (mirrors the session={} dict in ai-langgraph-agent/app.py but keyed by
#  session UUID so we can support multiple engineers at once)
# ---------------------------------------------------------------------------
_session_states: dict[str, dict] = {}
_state_lock = threading.Lock()


# ---------------------------------------------------------------------------
# POST /sessions
# ---------------------------------------------------------------------------

class CreateSessionBody(BaseModel):
    engineer_name: str
    github_username: str
    github_token: str


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    body: CreateSessionBody,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    """
    Admin creates a session for a departing engineer.
    GitHub analysis runs in the background so the response is immediate.
    """
    session = SessionModel(
        engineer_name=body.engineer_name,
        github_username=body.github_username,
        github_token=body.github_token,
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(
        _analyse_github_background,
        str(session.id),
        body.github_username,
        body.github_token,
    )

    return session


def _analyse_github_background(session_id: str, username: str, token: str):
    """
    Calls analyze_github() from ai-langgraph-agent, gets the first interview
    question, and stores everything so /chat can pick it up.
    """
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter_by(id=session_id).first()
        if not session:
            return

        # analyze_github returns: {profile, repos, master_document, knowledge_summary}
        analysis = analyze_github(username, token)

        # Prime the LangGraph agent with the GitHub summary
        state = {
            "github_summary": analysis["knowledge_summary"],
            "answer": "",
            "question": "",
            "history": [],
        }
        output = interview_agent.invoke(state)
        state["question"] = output["question"]

        with _state_lock:
            _session_states[session_id] = {
                "state": state,
                "analysis": analysis,
            }

        session.status = "interviewing"
        db.commit()

    except Exception as e:
        print(f"[GitHub analysis failed] {e}")
        if session:
            session.status = "failed"
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    """List all sessions ordered newest first."""
    return (
        db.query(SessionModel)
        .order_by(SessionModel.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
def chat(
    session_id: str,
    body: ChatRequest,
    db: DBSession = Depends(get_db),
):
    """
    Departing engineer sends an answer; gets the next interview question.
    Pass message="" to receive the very first question.
    """
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "pending":
        raise HTTPException(
            status_code=400,
            detail="GitHub analysis still in progress. Please wait.",
        )

    if session.status != "interviewing":
        raise HTTPException(
            status_code=400,
            detail=f"Session is in '{session.status}' state.",
        )

    with _state_lock:
        cached = _session_states.get(session_id)

    if not cached:
        raise HTTPException(
            status_code=500,
            detail="Session state lost. Please create a new session.",
        )

    state = cached["state"]

    # First call — just return the opening question, don't feed an answer yet
    if not body.message.strip():
        return ChatResponse(reply=state["question"], done=False)

    # Engineer answered — advance the LangGraph agent
    state["answer"] = body.message
    state["history"].append({
        "question": state["question"],
        "answer": body.message,
    })

    output = interview_agent.invoke(state)
    state["question"] = output["question"]

    with _state_lock:
        _session_states[session_id]["state"] = state

    # LangGraph agent doesn't signal done itself, so we cap at 8 exchanges
    done = len(state["history"]) >= 8
    if done:
        session.status = "done"
        db.commit()

    return ChatResponse(reply=state["question"], done=done)


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/slack
# ---------------------------------------------------------------------------

class SlackIngestBody(BaseModel):
    text: str


@router.post("/sessions/{session_id}/slack")
def ingest_slack(
    session_id: str,
    body: SlackIngestBody,
    db: DBSession = Depends(get_db),
):
    """
    Admin pastes raw Slack messages.
    Stored as knowledge chunks via the RAG vector store.
    """
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Import vector_store from backend root (where the backend team put it)
    _backend = Path(__file__).resolve().parent.parent
    sys.path.append(str(_backend))
    from vector_store import store_chunk

    chunks = body.text.split("\n\n")
    stored = 0
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        store_chunk(
            db=db,
            session_id=str(session_id),
            content=chunk,
            source="slack-paste",
            engineer_name=session.engineer_name,
            project_name="",
            chunk_type="slack",
        )
        stored += 1

    return {"stored_chunks": stored}


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    """
    Any engineer asks a plain-English question.
    Uses the RAG pipeline (retriever + Gemini) to return a cited answer.
    """
    docs = retrieve_relevant_context(body.question, k=5)

    if not docs:
        return AskResponse(
            answer="I don't have enough information in the knowledge base to answer that.",
            sources=[],
        )

    answer = generate_grounded_answer(body.question, docs)

    sources = [
        doc.metadata.get("source", "unspecified")
        for doc in docs
    ]

    return AskResponse(answer=answer, sources=sources)