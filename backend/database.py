"""
database.py — Shared database engine, session factory, and table initialisation.

Usage:
    from database import get_db, init_db

    # FastAPI dependency
    def my_route(db: Session = Depends(get_db)):
        ...

    # Call once at startup
    init_db()
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://archaeon:archaeon@localhost:5432/archaeon")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create the pgvector extension and all tables.
    Safe to call multiple times (CREATE IF NOT EXISTS semantics).
    """
    from models import Base  # local import to avoid circular import at module load

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)
    print("[database] Tables initialised.")
    