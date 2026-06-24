from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime

Base = declarative_base()

# ---------------------------------------------------------------------------
# Database Tables (SQLAlchemy)
# ---------------------------------------------------------------------------

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engineer_name = Column(String, nullable=False)
    github_username = Column(String, nullable=True)
    github_token = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, interviewing, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="session")
    chunks = relationship("KnowledgeChunk", back_populates="session")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "ai" or "engineer"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)  # "interview", "github", "slack"
    embedding = Column(Vector(384))

    # Metadata for RAG citations
    engineer_name = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    chunk_type = Column(String, nullable=True)  # "decision", "risk", "person", "service"

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chunks")


# ---------------------------------------------------------------------------
# Pydantic Models (API request/response shapes)
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    engineer_name: str
    github_username: str
    github_token: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    engineer_name: str
    github_username: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    done: bool


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str]