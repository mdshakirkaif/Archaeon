from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from github_analyzer import analyze_github
from interview_agent import interview_agent

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name="static")

session = {}

class StartRequest(BaseModel):
    github_username: str
    github_token: str

class AnswerRequest(BaseModel):
    answer: str

@app.get("/")
async def home():
    return FileResponse("templates/index.html")

@app.post("/start")
async def start(req: StartRequest):

    analysis = analyze_github(req.github_username,req.github_token)

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

    state = {"github_summary":github_summary,"answer": "","question": "","history": []}

    output = interview_agent.invoke(state)

    state["question"] = (output["question"])

    session["state"] = state

    return {"question":output["question"],"repo_cards":repo_cards,"profile": {"name":profile.get("name"),
            "avatar":profile.get("avatar_url")
        }
    }


@app.post("/answer")
async def answer(req: AnswerRequest):
    state = session["state"]

    state["answer"] = req.answer

    state["history"].append({"question":state["question"],"answer":req.answer})

    output = interview_agent.invoke(state)

    state["question"] = (output["question"])

    return {"question":output["question"]}

