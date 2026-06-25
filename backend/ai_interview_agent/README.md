# 🎙️ AI Offboarding Interview Agent

An AI-powered voice agent that interviews departing employees about their projects,
then automatically structures the captured knowledge into a report that helps new hires ramp up quickly.

---

## Folder structure

```
ai_interview_agent/
├── agent/
│   └── agent.py              ← Main voice agent (Alex)
├── connections/
│   └── github_analysis.py    ← Fetches GitHub commit history + Groq/Llama summary
├── output/                   ← JSON session files saved here after each interview
├── generate_report.py        ← Converts a JSON session → Markdown report
├── requirements.txt
├── .env.local                ← Fill in your API keys
└── README.md
```

---

## How it works

```
Frontend creates LiveKit room
  └─ metadata: { employee_name, project_name, github_username, github_org }
        │
        ▼
agent.py session starts
        │
        ├─► connections/github_analysis.py
        │       └─ Fetches commits from GitHub API (last 180 days)
        │       └─ Summarises with Llama-3.1 via Groq
        │       └─ Returns: top repos + AI summary of technical footprint
        │
        ├─► Summary injected silently into Alex's system prompt
        │
        ▼
Alex conducts voice interview (targeted at actual repos & code areas)
        │
        ▼
Session ends → transcript saved to output/*.json
        │
        ▼
python generate_report.py output/<file>.json
        │
        ▼
output/<file>_report.md  ← New hire reads this
```

---

## Quick start

### 1. Install dependencies

```bash
cd ai_interview_agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Fill in your API keys

Edit `.env.local` and add all keys listed there.

| Key | Where to get it |
|-----|----------------|
| `LIVEKIT_URL/API_KEY/SECRET` | [livekit.io](https://livekit.io) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `DEEPGRAM_API_KEY` | [deepgram.com](https://deepgram.com) |
| `CARTESIA_API_KEY` | [cartesia.ai](https://cartesia.ai) |
| `SIMLI_API_KEY/FACE_ID` | [simli.ai](https://simli.ai) |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |

### 3. Run the agent

```bash
python agent/agent.py start
```

### 4. Create a LiveKit room from your frontend

Pass room metadata so the agent knows who it's talking to:

```json
{
  "employee_name": "Alice Smith",
  "project_name":  "Payment Service",
  "github_username": "alice-github-handle",
  "github_org": "your-org-name"
}
```

`github_org` is optional. Leave it out for personal repos.

### 5. Generate a new-hire report after the session

```bash
# Specify a file
python generate_report.py output/offboarding_Alice_Smith_Payment_Service_20250601_120000.json

# Or omit the argument — it picks the latest file automatically
python generate_report.py
```

---

## Output files

### `output/*.json` — raw session data

```json
{
  "employee": "Alice Smith",
  "project": "Payment Service",
  "started_at": "2025-06-01T12:00:00",
  "ended_at":   "2025-06-01T13:10:00",
  "transcript": [
    { "role": "agent",    "text": "Can you walk me through...", "ts": "..." },
    { "role": "employee", "text": "Sure, this service...",      "ts": "..." }
  ],
  "summary": {
    "project_overview":        ["Handles all payment processing", "..."],
    "architecture_and_tech":   ["FastAPI + Postgres + Redis", "..."],
    "key_decisions":           ["Chose Stripe over Adyen because...", "..."],
    "known_issues_and_risks":  ["Webhook retry logic is flaky", "..."],
    "external_dependencies":   ["Stripe API", "Internal fraud service", "..."],
    "processes_and_workflows": ["Run `make dev` to start locally", "..."],
    "handover_tips":           ["Read ADR-001 first", "..."]
  }
}
```

### `output/*_report.md` — new-hire document

Clean Markdown with all 7 sections plus the full transcript. Ready to paste into
Confluence, Notion, or a GitHub wiki.

---

## Test GitHub analysis standalone

```bash
python connections/github_analysis.py
```

Set `GITHUB_USERNAME` in `.env.local` to the employee's handle before running.
