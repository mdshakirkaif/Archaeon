from __future__ import annotations

import threading

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from connectors.github import analyse_engineer
from connectors.slack import ingest_slack_text
from database import get_db
from models import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    KnowledgeChunk,
    Session as SessionModel,
    SessionResponse,
)
from pipelines.extraction import run_extraction
from pipelines.interview_agent import get_next_reply
from pipelines.retrieval import answer_question

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory cache for GitHub context per session (avoids re-fetching on
# every chat turn during the interview)
# ---------------------------------------------------------------------------
_github_context_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()


# ---------------------------------------------------------------------------
# POST /sessions
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    body: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    """
    Admin creates a new session for a departing engineer.

    What happens:
      1. Create a Session row (status=pending).
      2. In the background: call the GitHub connector to pull PRs and commit
         history, store PR chunks, and cache the context for the interview.
      3. Update status to "interviewing" when GitHub analysis completes.
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

    session_id = str(session.id)
    background_tasks.add_task(
        _analyse_github_background,
        session_id,
        body.github_username,
        body.github_token,
    )

    return session


def _analyse_github_background(session_id: str, username: str, token: str):
    """Background task: fetch GitHub data, cache context, update status."""
    from database import SessionLocal  # avoid circular import at module level

    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter_by(id=session_id).first()
        if not session:
            return

        context = analyse_engineer(username, token, session_id, db)

        with _cache_lock:
            _github_context_cache[session_id] = context

        session.status = "interviewing"
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    """Admin: list all sessions ordered by creation date descending."""
    sessions = (
        db.query(SessionModel)
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    return sessions


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/chat
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
def chat(
    session_id: str,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    """
Departing engineer sends a message (or empty string for the first question).

Returns the next AI question and done=True when the interview is finished.
When done=True the extraction pipeline is triggered automatically.
"""
session = db.query(SessionModel).filter_by(id=session_id).first()
if not session:
    raise HTTPException(status_code=404, detail="Session not found")

if session.status == "pending":
    raise HTTPException(
        status_code=400,
        detail="GitHub analysis still in progress.",
    )

if session.status != "interviewing":
    raise HTTPException(
        status_code=400,
        detail=f"Session is in '{session.status}' state.",
    )

with _cache_lock:
    github_context = _github_context_cache.get(session_id, {})

reply, done = get_next_reply(
    db_session=db,
    session=session,
    user_message=body.message,
    github_context=github_context,
)
    )

    if done:
        background_tasks.add_task(_run_extraction_background, session_id)

    return ChatResponse(reply=reply, done=done)


def _run_extraction_background(session_id: str):
    """Background task: run extraction pipeline after interview completes."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter_by(id=session_id).first()
        if session:
            run_extraction(db, session)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/slack
# ---------------------------------------------------------------------------

class SlackIngestRequest:
    pass


from pydantic import BaseModel


class SlackIngestBody(BaseModel):
    text: str


@router.post("/sessions/{session_id}/slack")
def ingest_slack(
    session_id: str,
    body: SlackIngestBody,
    db: DBSession = Depends(get_db),
):
    """
    Admin pastes raw Slack messages for the session.
    The text is chunked, embedded, and stored as knowledge chunks.
    """
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    count = ingest_slack_text(body.text, session_id, db)
    return {"stored_chunks": count}


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------

@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    db: DBSession = Depends(get_db),
):
    """
    Any engineer asks a question in plain English.
    Returns a cited answer drawn from the knowledge base.
    """
    answer, sources = answer_question(body.question, db)
    return AskResponse(answer=answer, sources=sources)