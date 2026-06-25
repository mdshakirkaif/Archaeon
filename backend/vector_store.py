"""
vector_store.py
Two functions:
  - store_chunk(): converts text to embedding and saves to knowledge_chunks table
  - search_chunks(): finds the most similar chunks to a question using vector search
"""

import uuid
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from models import KnowledgeChunk

# Load the embedding model once when the file is imported
model = SentenceTransformer('all-MiniLM-L6-v2')


def get_embedding(text: str) -> list:
    """Convert text to a list of numbers (embedding)."""
    return model.encode(text).tolist()


def store_chunk(
    db: Session,
    session_id: uuid.UUID,
    content: str,
    source: str,
    engineer_name: str = None,
    project_name: str = None,
    chunk_type: str = None,
):
    embedding = get_embedding(content)

    chunk = KnowledgeChunk(
        session_id=session_id,
        content=content,
        source=source,
        embedding=embedding,
        engineer_name=engineer_name,
        project_name=project_name,
        chunk_type=chunk_type,
    )

    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def search_chunks(
    db: Session,
    question: str,
    limit: int = 5,
) -> list:
    question_embedding = get_embedding(question)

    results = (
        db.query(KnowledgeChunk)
        .order_by(
            KnowledgeChunk.embedding.l2_distance(question_embedding)
        )
        .limit(limit)
        .all()
    )

    return results