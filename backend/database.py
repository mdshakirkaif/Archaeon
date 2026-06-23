import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    return conn

async def init_db():
    conn = await get_connection()
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.close()
    print("✅ Database initialized successfully!")
    