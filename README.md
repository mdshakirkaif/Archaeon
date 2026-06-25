# Archaeon

Preserve institutional engineering knowledge when engineers leave. AI-powered interviews, knowledge graph extraction, and cited Q&A.

## Prerequisites

- **Node.js** 18+ (frontend)
- **Python** 3.11+ (backend)
- **Docker** (PostgreSQL + pgvector)
- **Chrome** (speech recognition doesn't work on Edge/Firefox)

## Quick Start

### 1. Database

```bash
docker-compose up -d
```

Starts PostgreSQL 16 with pgvector on `localhost:5432`.

**If you get schema errors** (missing columns, wrong embedding dimensions), reset:

```bash
docker-compose down -v
docker-compose up -d
```

Tables auto-create on first backend run via `init_db()`.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r ../requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://archaeon:archaeon@localhost:5432/archaeon
GOOGLE_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-3.1-flash-lite
```

Run the server:

```bash
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

**New 3-step flow:**

1. Go to `/admin` → Register tab → Enter engineer name, GitHub username, and token
2. Backend fetches repos → repo selection table appears → **Select which repos to analyze**
3. Click "Start Interview" → AI conducts the knowledge-transfer interview (Chrome for speech)
4. Go to `/qa` → Ask questions → Get cited answers from captured knowledge (interview + Slack)

**Flow states:**
- `pending` — backend is fetching repos
- `repos_ready` — repo list available for selection
- `interviewing` — interview in progress
- `done` — interview complete

## Architecture

- **Frontend:** React + Vite, port 3000
- **Backend:** FastAPI, port 8000
- **Database:** PostgreSQL 16 + pgvector (Docker)
- **AI:** LangGraph agent (interview), Gemini 2.5 Flash (RAG), all-MiniLM-L6-v2 (embeddings)

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions` | Create session, fetch repos |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}/repos` | Get repo list for selection |
| POST | `/api/sessions/{id}/start-interview` | Start interview with selected repos |
| POST | `/api/sessions/{id}/chat` | Submit answer, get next question |
| POST | `/api/sessions/{id}/slack` | Ingest Slack messages |
| POST | `/api/ask` | Ask RAG question |

## Notes

- Interview answers are saved to the `knowledge_chunks` vector DB automatically — Q&A can search them
- 5-question cap on interviews
- Each developer runs their own local Postgres — data is not shared between machines
- Vite proxy forwards `/api/*` to `http://localhost:8000/*` (strips `/api` prefix)
