# Archaeon — Issues & Fixes Tracker

> **From:** Abhay (Frontend)
> **Last updated:** 2026-06-24
> **Context:** Frontend fully built, lint-clean, build-passing. Backend has blocking issues preventing end-to-end testing.

---

## Frontend Status

| Check | Status |
|-------|--------|
| `npm run build` | **Pass** — clean production build |
| `npm run lint` | **Pass** — zero errors, zero warnings |
| TypeScript | N/A (plain React/Vite) |

### Frontend fixes applied (this session)

| File | Fix |
|------|-----|
| `api.js` | Removed unused import `resetDemoQuestions`, removed unused `sessionId` param from `getQaHistory` |
| `demo.js` | Removed unused params `sessionId` from `demoGetNextQuestion`, `sessionId`/`audioBlob` from `demoUploadAnswer` |
| `Admin.jsx` | Removed unused `sc` variable |
| `InterviewConsole.jsx` | Suppressed intentional missing dep warning for `loadQuestion` (StrictMode guard) |
| `QAScreen.jsx` | Fixed `setState` in effect — now initializes state directly from `localStorage` via lazy initializer |

---

## CRITICAL — Backend won't start

### 1. `routes.py` imports non-existent module

**File:** `backend/api/routes.py:9`
**Severity:** FATAL — `ModuleNotFoundError` on startup

```python
from connectors.github import analyse_engineer  # WRONG
```

`connectors/github.py` does not exist. The file is `connectors/github_analysis.py`.

**Fix:** Change to `from connectors.github_analysis import analyse_engineer` AND add an `analyse_engineer()` wrapper function to `github_analysis.py` (the file only has `class GitHubAnalyzer`, not a standalone function).

---

### 2. `routes.py` imports functions that don't exist

**File:** `backend/api/routes.py:10, 21-23`
**Severity:** FATAL — `ImportError` on startup

| Line | Import | Problem |
|------|--------|---------|
| 10 | `from connectors.slack import ingest_slack_text` | `slack.py` has `class SlackAnalyzer`, no `ingest_slack_text` function |
| 21 | `from pipelines.extraction import run_extraction` | `extraction.py` has `class ExtractionPipeline`, no `run_extraction` function |
| 22 | `from pipelines.interview_agent import get_next_reply` | `interview_agent.py` has `class InterviewAgentPipeline`, no `get_next_reply` function |
| 23 | `from pipelines.retrieval import answer_question` | `retrieval.py` has `class RetrievalPipeline`, no `answer_question` function |

**Fix:** Add these wrapper functions to each file:

- `github_analysis.py` — `analyse_engineer(username, token, session_id, db) -> dict`
- `slack.py` — `ingest_slack_text(text, session_id, db) -> int`
- `extraction.py` — `run_extraction(db, session) -> None`
- `interview_agent.py` — `get_next_reply(db_session, session, user_message, github_context) -> tuple[str, bool]` with `_QUESTIONS` list (5 questions) and Message row storage
- `retrieval.py` — `answer_question(question, db) -> tuple[str, list[str]]`

---

## BLOCKING — API endpoints return errors

### 3. `POST /chat` returns 500 (no interview logic)

**Endpoint:** `POST /api/sessions/{id}/chat`
**Severity:** HIGH — Interview page can't load questions

Even if imports are fixed, `get_next_reply()` doesn't exist on remote. The backend has an empty `InterviewAgentPipeline` class stub with no question logic.

**Fix:** Add `get_next_reply()` that:
- Counts existing AI messages for the session (`role="ai"`)
- Stores the engineer's answer as a Message row (if non-empty)
- Returns the next question from a `_QUESTIONS` list
- Returns `done=True` after all questions asked

---

### 4. `POST /ask` returns 500 (no retrieval logic)

**Endpoint:** `POST /api/ask`
**Severity:** HIGH — Q&A page can't answer questions

`answer_question()` doesn't exist. `retrieval.py` is an empty stub.

**Fix:** Add `answer_question(question, db) -> tuple[str, list[str]]` that queries KnowledgeChunks and returns an answer + sources.

---

### 5. `POST /slack` returns 500 (no ingest logic)

**Endpoint:** `POST /api/sessions/{id}/slack`
**Severity:** MEDIUM — Admin can't paste Slack messages

`ingest_slack_text()` doesn't exist. `slack.py` only has `SlackAnalyzer` class.

**Fix:** Add `ingest_slack_text(text, session_id, db) -> int` that chunks the text and stores as KnowledgeChunks with `source="slack"`.

---

### 6. Background GitHub analysis fails

**Endpoint:** `POST /api/sessions` triggers background task
**Severity:** MEDIUM — Session stays `pending` forever, interview can't start

`analyse_engineer()` wrapper doesn't exist. The background task in `routes.py` calls `analyse_engineer(username, token, session_id, db)` but `GitHubAnalyzer` is async with different parameters.

**Fix:** Add `analyse_engineer()` wrapper that:
- Instantiates `GitHubAnalyzer`
- Runs `run_analysis(username)` via `asyncio.get_event_loop()`
- Returns the analysis dict
- Handles errors gracefully (don't crash background task)

---

## NOT BLOCKING (but needs fixing eventually)

### 7. Response shape mismatch

**Files:** `backend/models.py` vs `frontend/src/api.js`

| Endpoint | Backend returns | Frontend expects | Frontend handling |
|----------|----------------|------------------|-------------------|
| `POST /chat` | `{reply, done}` | `{question, index, total, done}` | Mapped in `api.js` |
| `POST /ask` | `{answer, sources: string[]}` | `{answer, citations: [{source, snippet}]}` | Mapped in `api.js` |

**Frontend handles this.** Backend can align later.

---

## LiveKit Voice Agent (kaif's work)

**Location:** `backend/ai_interview_agent/`
**Status:** Standalone system, NOT integrated with FastAPI or React frontend yet

kaif built a separate LiveKit-based voice interview agent with:
- Deepgram STT (speech-to-text)
- Cartesia TTS (text-to-speech)
- Simli avatar
- GitHub analyzer
- Report generator

**Frontend impact:** When kaif finishes integrating this with the FastAPI backend, we'll need to update `InterviewConsole.jsx` to use LiveKit client instead of MediaRecorder + Web Speech API.

**Waiting on:** kaif's integration code before updating frontend interview screens.

---

## Summary

| # | Issue | Severity | Status | Fix needed in |
|---|-------|----------|--------|---------------|
| 1 | Wrong import (`connectors.github`) | FATAL | Open | `routes.py` + `github_analysis.py` |
| 2 | Missing functions (4 imports) | FATAL | Open | `slack.py`, `extraction.py`, `interview_agent.py`, `retrieval.py` |
| 3 | No interview question logic | HIGH | Open | `interview_agent.py` |
| 4 | No retrieval/Q&A logic | HIGH | Open | `retrieval.py` |
| 5 | No Slack ingest logic | MEDIUM | Open | `slack.py` |
| 6 | No `analyse_engineer` wrapper | MEDIUM | Open | `github_analysis.py` |
| 7 | Response shape mismatch | LOW | **Fixed in frontend** | `api.js` maps shapes |

**Once issues 1-6 are fixed, the frontend should work end-to-end.**
