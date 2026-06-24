import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Allow importing from connections/
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'connections'))
from github_analysis import GitHubAnalyzer

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import anthropic, simli

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge capture — records transcript, flushed to JSON at session end
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeCapture:
    def __init__(self, employee_name: str, project_name: str):
        self.employee_name = employee_name
        self.project_name = project_name
        self.started_at = datetime.utcnow().isoformat()
        self.transcript: list[dict] = []
        self.summary_sections: dict[str, list[str]] = {
            "project_overview": [],
            "architecture_and_tech": [],
            "key_decisions": [],
            "known_issues_and_risks": [],
            "external_dependencies": [],
            "processes_and_workflows": [],
            "handover_tips": [],
        }

    def add_turn(self, role: str, text: str):
        self.transcript.append({
            "role": role,
            "text": text,
            "ts": datetime.utcnow().isoformat()
        })

    def save(self, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        slug = (
            f"{self.employee_name.replace(' ', '_')}_"
            f"{self.project_name.replace(' ', '_')}"
        )
        filename = f"offboarding_{slug}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(output_dir, filename)
        payload = {
            "employee": self.employee_name,
            "project": self.project_name,
            "started_at": self.started_at,
            "ended_at": datetime.utcnow().isoformat(),
            "transcript": self.transcript,
            "summary": self.summary_sections,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[KnowledgeCapture] Session saved → {path}")
        return path


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────

class OffboardingAgent(Agent):
    """
    AI interviewer (Alex) that extracts deep project knowledge from a departing
    employee. GitHub footprint is injected as hidden context so questions are
    targeted at the employee's actual repos and commit history.
    """

    def __init__(self, github_context: str = "") -> None:

        github_section = ""
        if github_context:
            github_section = (
                f"\n\nGITHUB FOOTPRINT ANALYSIS (use this to guide your questions — "
                f"do NOT read it aloud or mention it directly):\n"
                f"{github_context}\n\n"
                "Use the above to ask specific questions about the repos, fragile areas, "
                "and components the employee actually worked on. Reference them naturally "
                "as if you already know the project context.\n"
            )

        super().__init__(
            instructions=(
                "Your name is Alex and you are a senior technical knowledge transfer specialist. "
                "You are interviewing a departing employee to capture everything a new engineer "
                "would need to understand and continue their project. "
                "Keep all responses short and conversational — this is a voice interaction. "
                "Never use formatting, bullet points, emojis, or special characters in your speech.\n\n"

                "Your interview covers these topics in order, but stay flexible:\n"
                "1. Project overview — what does the project do, who uses it, why does it exist?\n"
                "2. Architecture and tech stack — how is it built, what are the main components?\n"
                "3. Key design decisions — what were the important choices made and why?\n"
                "4. Known issues and technical debt — what is broken, slow, or needs attention?\n"
                "5. External dependencies — third-party services, APIs, teams they collaborate with?\n"
                "6. Day-to-day workflows — how to run it locally, deploy it, monitor it?\n"
                "7. Handover tips — what would they tell a new engineer on day one?\n\n"

                "Rules:\n"
                "- Ask one focused question at a time.\n"
                "- After each answer, acknowledge briefly (one sentence), then ask a smart follow-up "
                "or naturally transition to the next topic.\n"
                "- If an answer is vague, probe deeper before moving on.\n"
                "- If the employee mentions a tool, service, or acronym, ask them to explain it "
                "briefly so the knowledge base is complete.\n"
                "- About every five exchanges, do a quick recap of what you have learned so far "
                "and confirm accuracy with the employee.\n"
                "- Near the end, always ask: Is there anything critical that I have not asked about yet?\n"
                "- Be warm, respectful, and make the employee feel their knowledge is truly valued.\n"
                "- This is not an evaluation — there are no wrong answers.\n"
                + github_section
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Server + session wiring
# ─────────────────────────────────────────────────────────────────────────────

server = AgentServer()


@server.rtc_session(agent_name="offboarding-agent")
async def offboarding_session(ctx: agents.JobContext):

    # Parse room metadata passed from the frontend
    meta = ctx.room.metadata or "{}"
    try:
        room_data = json.loads(meta)
    except json.JSONDecodeError:
        room_data = {}

    employee_name   = room_data.get("employee_name",   "Employee")
    project_name    = room_data.get("project_name",    "the project")
    github_username = room_data.get("github_username", "")
    github_org      = room_data.get("github_org",      None)

    capture = KnowledgeCapture(employee_name, project_name)

    # ── Fetch GitHub footprint before starting the session ───────────────────
    github_context = ""
    if github_username:
        print(f"[GitHub] Fetching footprint for '{github_username}'...")
        try:
            analyzer = GitHubAnalyzer()
            analysis = await analyzer.run_analysis(username=github_username, org=github_org)
            github_context = analysis.get("ai_summary", "")
            top = analysis.get("services", [])
            print(f"[GitHub] Done. Top services: {top}")
        except Exception as e:
            print(f"[GitHub] Analysis failed (continuing without it): {e}")

    # ── LiveKit session ──────────────────────────────────────────────────────
    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm=anthropic.LLM(model="claude-sonnet-4-20250514"),
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
    )

    # ── Simli Avatar ─────────────────────────────────────────────────────────
    avatar = simli.AvatarSession(
        simli_config=simli.SimliConfig(
            api_key=os.getenv("SIMLI_API_KEY"),
            face_id=os.getenv("SIMLI_FACE_ID"),
        ),
        avatar_participant_name="alex-avatar",
    )
    await avatar.start(session, room=ctx.room)

    # ── Transcript hooks ─────────────────────────────────────────────────────
    @session.on("user_speech_committed")
    def on_user(event):
        capture.add_turn("employee", event.alternatives[0].text)

    @session.on("agent_speech_committed")
    def on_agent(event):
        capture.add_turn("agent", event.text)

    # ── Session teardown — auto-summarise + save ─────────────────────────────
    @session.on("close")
    async def on_close(_event):
        try:
            transcript_text = "\n".join(
                f"{t['role'].upper()}: {t['text']}" for t in capture.transcript
            )
            summary_prompt = (
                f"You are a technical writer. Below is a transcript of an offboarding interview "
                f"with {employee_name} about the project '{project_name}'. "
                f"Extract concise bullet points for each section and return ONLY valid JSON "
                f"with these keys: project_overview, architecture_and_tech, key_decisions, "
                f"known_issues_and_risks, external_dependencies, processes_and_workflows, handover_tips. "
                f"Each key maps to a list of strings.\n\nTRANSCRIPT:\n{transcript_text}"
            )
            import anthropic as _anthropic
            client = _anthropic.Anthropic()
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": summary_prompt}],
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            capture.summary_sections = json.loads(raw)
        except Exception as e:
            print(f"[Summary] Could not auto-summarise: {e}")

        capture.save()

    # ── Start the session ────────────────────────────────────────────────────
    await session.start(
        room=ctx.room,
        agent=OffboardingAgent(github_context=github_context),
    )

    greeting = (
        f"Hi {employee_name}, I am Alex. "
        f"Thank you so much for taking the time to do this knowledge transfer session. "
        f"My job today is to capture everything important about {project_name} "
        f"so that the next engineer who picks it up can hit the ground running. "
        f"This is not an evaluation at all, just a conversation. "
        f"Let us start with the basics. "
        f"Can you give me a quick overview of what {project_name} does "
        f"and who the main users or stakeholders are?"
    )
    await session.generate_reply(instructions=greeting)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agents.cli.run_app(server)
