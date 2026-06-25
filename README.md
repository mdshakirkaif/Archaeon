# Archaeon

Preserve institutional engineering knowledge when engineers leave. AI-powered interviews, knowledge graph extraction, and cited Q&A.

## Prerequisites

- **Node.js** 18+ (frontend)
- **Python** 3.11+ (backend)
- **Docker** (for PostgreSQL + pgvector)
- **Chrome** (speech recognition doesn't work on Edge/Firefox)

## Quick Start

### 1. Database

```bash
docker-compose up -d
```

Starts PostgreSQL 16 with pgvector on `localhost:5432`.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux
pip install -r ../requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://archaeon:archaeon@localhost:5432/archaeon
GROQ_API_KEY=your-groq-key
GOOGLE_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-3.1-flash-lite
```

Run the server:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000`.

## Usage

1. Go to `/admin` — register an engineer (name + GitHub username + token)
2. Go to `/interview/:id` — AI conducts the knowledge-transfer interview (use Chrome for speech)
3. Go to `/qa` — ask questions, get cited answers from the captured knowledge

## Demo Mode

Click "Try Demo" on the homepage to explore with mock data (no backend needed).

## Architecture

- **Frontend:** React + Vite, port 3000
- **Backend:** FastAPI, port 8000
- **Database:** PostgreSQL 16 + pgvector (Docker)
- **AI:** LangGraph agent (interview), Gemini (RAG generation), all-MiniLM-L6-v2 (embeddings)
