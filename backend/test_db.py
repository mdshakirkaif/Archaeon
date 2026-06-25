import psycopg2
import os
from dotenv import load_dotenv
from database import init_db, SessionLocal
from models import Session
from vector_store import store_chunk, search_chunks

load_dotenv()

# Test raw connection
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    print("✅ Database connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")

# Create tables
init_db()

db = SessionLocal()

# Create a real session first
test_session = Session(
    engineer_name="John",
    github_username="john_dev",
    github_token="fake_token_for_testing",
    status="completed"
)
db.add(test_session)
db.commit()
db.refresh(test_session)
print(f"✅ Session created: {test_session.id}")

# Store a chunk using the real session id
store_chunk(
    db=db,
    session_id=str(test_session.id),
    content="The payment service retries 3 times because the bank API times out on first try",
    source="interview",
    engineer_name="John",
    project_name="payments-service",
    chunk_type="decision"
)
print("✅ Chunk stored!")

# Search for it
results = search_chunks(db, "why does payment retry?")
for r in results:
    print(f"Found: {r.content} — by {r.engineer_name} on {r.project_name}")

db.close()