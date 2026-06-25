import sys
from pathlib import Path

# Path patch to find vector_store.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from vector_store import store_chunk
from retriever import retrieve_relevant_context
from generator import generate_grounded_answer
import config

def test_pipeline():
    print(f"Connecting to database via: {config.POSTGRES_URL}")
    engine = create_engine(config.POSTGRES_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Test basic connection (The "Ping")
        print("\n--- STEP 1: Testing Connection ---")
        db.execute(text("SELECT 1"))
        print("SUCCESS: Database connection verified!")
        
        # Step 2: Insert a mock chunk to test the backend team's store function
        print("\n--- STEP 2: Inserting Mock Context Data ---")
        mock_text = (
            "During his departure interview, Tanishq noted that the payment processing system "
            "uses Stripe Connect. He emphasized that the webhook signing secret must be rotated "
            "every 90 days in the production environment variables to prevent token expiration issues."
        )
        
        store_chunk(
            db=db,
            session_id="test_session_123",
            content=mock_text,
            source="exit_interview_tanishq.txt",
            engineer_name="Tanishq",
            project_name="Payment Gateway",
            chunk_type="interview"
        )
        print("SUCCESS: Mock engineering text vectorized and saved into knowledge_chunks!")
        
        # Step 3: Run your retriever search
        print("\n--- STEP 3: Testing Retrieval Engine ---")
        query = "What did Tanishq say about the webhook signing secret?"
        matching_chunks = retrieve_relevant_context(query, k=1)
        
        if matching_chunks:
            print(f"SUCCESS: Found matching text fragment from source: {matching_chunks[0].metadata['source']}")
            
            # Step 4: Run your generation loop
            print("\n--- STEP 4: Testing Gemini LLM Generation ---")
            answer = generate_grounded_answer(query, matching_chunks)
            print(f"\nFinal AI Response:\n{answer}\n")
        else:
            print("FAILED: No chunks retrieved. Check if vector dimensions or embeddings match.")
            
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_pipeline()