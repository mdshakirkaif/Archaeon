from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes import router

app = FastAPI(
    title="Archaeon",
    description=(
        "Preserve institutional engineering knowledge when engineers leave. "
        "AI-powered interviews, knowledge graph extraction, and cited Q&A."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)



@app.on_event("startup")
def startup():
    """Create DB tables and pgvector extension on first run."""
    init_db()



@app.get("/health")
def health():
    return {"status": "ok"}