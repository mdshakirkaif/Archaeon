from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from github_analyzer import analyze_github
from interview_agent import interview_agent

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal, init_db
from vector_store import store_chunk

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

session = {}

class StartRequest(BaseModel):
    github_username: str
    github_token: str

class AnswerRequest(BaseModel):
    answer: str

@app.on_event("startup")
def startup():
    """Initialize database tables on startup."""
    init_db()

@app.get("/")
async def home():
    return FileResponse("templates/index.html")

@app.post("/start")
async def start(req: StartRequest):

    analysis = analyze_github(req.github_username, req.github_token)

    profile = analysis["profile"]
    repos = analysis["repos"]
    github_summary = analysis["knowledge_summary"]

    repo_cards = ""
    for repo in repos:
        repo_cards += f"""
        <div class='repo-card'>
            <h3>{repo['name']}</h3>
            <p>{repo.get('language')}</p>
            <p>{repo.get('description')}</p>
        </div>
        """

    state = {
        "github_summary": github_summary,
        "answer": "",
        "question": "",
        "history": []
    }

    output = interview_agent.invoke(state)
    state["question"] = output["question"]

    # Store session info including github_username
    session["state"] = state
    session["github_username"] = req.github_username
    session["github_token"] = req.github_token

    return {
        "question": output["question"],
        "repo_cards": repo_cards,
        "profile": {
            "name": profile.get("name"),
            "avatar": profile.get("avatar_url")
        }
    }


@app.post("/answer")
async def answer(req: AnswerRequest):
    state = session["state"]
    github_username = session["github_username"]

    state["answer"] = req.answer
    state["history"].append({
        "question": state["question"],
        "answer": req.answer
    })

    # Save the Q&A pair to vector database
    db = SessionLocal()
    try:
        content = f"Question: {state['question']}\nAnswer: {req.answer}"

        store_chunk(
            db=db,
            session_id="00000000-0000-0000-0000-000000000000",  # placeholder until real sessions
            content=content,
            source="interview",
            engineer_name=github_username,  # using github username as metadata for now
            project_name=None,
            chunk_type="qa"
        )
    finally:
        db.close()

    output = interview_agent.invoke(state)
    state["question"] = output["question"]

    return {"question": output["question"]}