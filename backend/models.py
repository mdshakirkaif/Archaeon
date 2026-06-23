from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engineer_name = Column(String, nullable=False)
    github_token = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, active, completed
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
    embedding = Column(Vector(768))
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chunks")