import os
from pathlib import Path
from dotenv import load_dotenv

# Force it to look directly inside the backend/rag folder for the .env
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"

load_dotenv(dotenv_path=env_path)

TEST_MODE = False

# Fallback print statement to debug what SQLAlchemy is actually seeing
POSTGRES_URL = os.getenv("POSTGRES_URL")

if not POSTGRES_URL:
    # If it's still empty, try checking for the team's default backend variable name
    POSTGRES_URL = os.getenv("DATABASE_URL")

# Clean fallback string format check
if not POSTGRES_URL:
    POSTGRES_URL = "postgresql://archaeon:archaeon@localhost:5432/archaeon"

LLM_MODEL = "gemini-3.1-flash-lite"