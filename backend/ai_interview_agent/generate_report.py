"""
generate_report.py
──────────────────
Reads a JSON session file saved after an offboarding interview and produces
a clean Markdown knowledge-transfer report for new hires.

Usage:
    python generate_report.py output/offboarding_Alice_Smith_PaymentService_20250601_120000.json
"""

import json
import sys
import os
from datetime import datetime


SECTION_TITLES = {
    "project_overview":        "📦 Project Overview",
    "architecture_and_tech":   "🏗️  Architecture & Tech Stack",
    "key_decisions":           "🧠 Key Design Decisions",
    "known_issues_and_risks":  "⚠️  Known Issues & Technical Debt",
    "external_dependencies":   "🔗 External Dependencies",
    "processes_and_workflows": "⚙️  Processes & Workflows",
    "handover_tips":           "💡 Day-One Tips for the New Engineer",
}


def render_markdown(data: dict) -> str:
    employee = data.get("employee", "Unknown")
    project  = data.get("project",  "Unknown")
    started  = data.get("started_at", "")

    lines = [
        f"# Knowledge Transfer Report: {project}",
        f"",
        f"> **Captured from:** {employee}  ",
        f"> **Session date:** {started[:10] if started else 'N/A'}  ",
        f"> **Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"",
        f"---",
        f"",
    ]

    summary = data.get("summary", {})
    for key, title in SECTION_TITLES.items():
        items = summary.get(key, [])
        lines.append(f"## {title}")
        lines.append("")
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("_No information captured for this section._")
        lines.append("")

    lines += [
        "---",
        "",
        "## 📝 Full Interview Transcript",
        "",
        "_The raw conversation for deeper context._",
        "",
    ]

    transcript = data.get("transcript", [])
    for turn in transcript:
        role  = turn.get("role", "unknown").capitalize()
        text  = turn.get("text", "")
        ts    = turn.get("ts", "")[:19].replace("T", " ")
        prefix = "**Alex (AI):**" if role == "Agent" else f"**{employee}:**"
        lines.append(f"> {prefix} {text}  ")
        lines.append(f"> <sub>{ts}</sub>")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        # Auto-pick latest file in output/ if no arg given
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        files = sorted(
            [f for f in os.listdir(output_dir) if f.endswith(".json")],
            reverse=True
        )
        if not files:
            print("No JSON session files found in output/")
            print("Usage: python generate_report.py output/<filename>.json")
            sys.exit(1)
        json_path = os.path.join(output_dir, files[0])
        print(f"No file specified — using latest: {json_path}")
    else:
        json_path = sys.argv[1]

    with open(json_path) as f:
        data = json.load(f)

    md = render_markdown(data)
    out_path = json_path.replace(".json", "_report.md")
    with open(out_path, "w") as f:
        f.write(md)

    print(f"✅ Report written → {out_path}")


if __name__ == "__main__":
    main()
