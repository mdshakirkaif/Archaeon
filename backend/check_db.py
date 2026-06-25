from database import SessionLocal
from models import KnowledgeChunk, Session

db = SessionLocal()

sessions = db.query(Session).all()
print(f"Total sessions: {len(sessions)}")
for s in sessions:
    print(f"  - {s.engineer_name} ({s.github_username}) — {s.status}")

chunks = db.query(KnowledgeChunk).all()
print(f"\nTotal knowledge chunks: {len(chunks)}")
for c in chunks:
    print(f"  - [{c.source}] {c.engineer_name}: {c.content[:80]}...")

db.close()