import sys
from pathlib import Path

# This allows Python to look one directory level up to find vector_store.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_core.documents import Document

# Now we can safely import their database search utility
from vector_store import search_chunks
import config

engine = create_engine(config.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def retrieve_relevant_context(query, k=2):
    db = SessionLocal()
    try:
        raw_chunks = search_chunks(db=db, question=query, limit=k)
        
        docs = []
        for chunk in raw_chunks:
            metadata = {
                "source": chunk.source or "unspecified",
                "engineer_name": chunk.engineer_name,
                "project_name": chunk.project_name,
                "chunk_type": chunk.chunk_type,
                "session_id": chunk.session_id
            }
            docs.append(Document(page_content=chunk.content, metadata=metadata))
            
        return docs
        
    except Exception as error:
        print(f"Database lookup failed: {error}")
        return []
    finally:
        db.close()