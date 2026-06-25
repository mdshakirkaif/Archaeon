# test_connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vector_store import search_chunks
import config

def test_db_lookup():
    print(f"Testing database connection via: {config.POSTGRES_URL}")
    engine = create_engine(config.POSTGRES_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("Running an initial vector lookup test for 'auth service'...")
        results = search_chunks(db=db, question="auth service", limit=1)
        print(f"Successfully retrieved {len(results)} chunks from knowledge_chunks table.")
        for chunk in results:
            print(f"Sample source found: {chunk.source}")
    except Exception as e:
        print(f"Connection test failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db_lookup()