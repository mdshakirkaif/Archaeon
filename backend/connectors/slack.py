import os
import httpx
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio
from dotenv import load_dotenv

load_dotenv()

class SlackAnalyzer:
    def __init__(self):
        # Requires a Slack User Token (xoxp-...) or Bot Token (xoxb-...) with history read scopes
        self.token = os.getenv("SLACK_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://slack.com/api"

    async def _get_public_channels(self) -> list:
        """Fetches list of accessible public channels in the workspace."""
        if not self.token:
            print("[WARNING] SLACK_TOKEN not found. Using local fallback channels.")
            return ["dummy-dev-talk", "dummy-prod-incidents"]

        url = f"{self.base_url}/conversations.list"
        params = {"types": "public_channel", "limit": 100}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                data = response.json()
                if response.status_code == 200 and data.get("ok"):
                    return [ch["id"] for ch in data["channels"]]
                else:
                    print(f"[SLACK API ERROR] Failed to fetch channels: {data.get('error')}")
                    return []
        except Exception as e:
            print(f"Error fetching Slack channels: {e}")
            return []

    async def run_analysis(self, user_slack_id: str) -> dict:
        """Scans Slack conversation history footprints and extracts inline communication context."""
        # Calculate time cutoff (180 days ago in epoch timestamp units for Slack API)
        six_months_ago = datetime.now() - timedelta(days=180)
        oldest_timestamp = str(six_months_ago.timestamp())
        
        channels = await self._get_public_channels()
        targeted_messages = []
        message_density = {}

        print(f"Scanning {len(channels)} Slack channels for messages from user '{user_slack_id}' over the last 180 days...")

        # Context keywords that pinpoint core decisions, legacy issues, or architectural fragility
        critical_keywords = ["bug", "fix", "fragile", "broke", "decision", "why", "workaround", "rewrite", "legacy"]

        for channel in channels:
            url = f"{self.base_url}/conversations.history"
            params = {
                "channel": channel,
                "oldest": oldest_timestamp,
                "limit": 200
            }
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    data = response.json()
                    
                    if response.status_code == 200 and data.get("ok"):
                        messages = data.get("messages", [])
                        
                        # Filter down to messages explicitly authored by this user
                        user_messages = [m for m in messages if m.get("user") == user_slack_id]
                        
                        if user_messages:
                            message_density[channel] = len(user_messages)
                            
                            for m in user_messages:
                                text = m.get("text", "")
                                # Flag if the message contains technical context signals
                                is_high_value = any(kw in text.lower() for kw in critical_keywords)
                                
                                targeted_messages.append({
                                    "channel": channel,
                                    "text": text,
                                    "is_high_value": is_high_value
                                })
            except Exception as e:
                print(f"Skipping channel {channel} due to connection error: {e}")

        # Sort out channels where they are most talkative/assertive
        top_channels = sorted(message_density, key=message_density.get, reverse=True)[:3]
        
        # Isolate high-value context conversations to pass to the LLM context pool
        high_value_logs = [m for m in targeted_messages if m["is_high_value"]]
        # Fallback to general logs if no explicit keyword matches hit
        context_pool = high_value_logs if high_value_logs else targeted_messages

        slack_summary_text = (
            f"User {user_slack_id} interacted across {len(message_density)} channels, "
            f"submitting {len(targeted_messages)} total messages. Most active in: {', '.join(top_channels) if top_channels else 'none'}."
        )

        # Build clean log arrays for Groq context ingestion
        formatted_logs = [f"Channel: {m['channel']} | Msg: {m['text']}" for m in context_pool]
        input_text = f"Summary Data: {slack_summary_text}\n\nHigh-Value Context Logs:\n" + "\n".join(formatted_logs[:50])

        # Run Groq Llama Summary
        ai_summary = self._generate_groq_summary(input_text)

        return {
            "slack_user_id": user_slack_id,
            "top_channels": top_channels,
            "ai_summary": ai_summary
        }

    def _generate_groq_summary(self, content: str) -> str:
        if not os.getenv("GROQ_API_KEY"):
            return "Error: GROQ_API_KEY environment variable not set."

        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",
            temperature=0.2,
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", (
                "You are Archaeon's expert communication analyst. Summarize the raw Slack chat history "
                "of a departing engineer. Identify specific technical decisions they defended, systems "
                "they helped troubleshoot, architectural changes they announced, or implicit codebase risks they complained about.\n\n"
                "Format output in markdown with concise bullet points."
            )),
            ("user", "Please summarize the technical footprint from this raw chat data:\n\n{text}")
        ])

        chain = prompt_template | llm | StrOutputParser()

        try:
            print("\nAnalyzing Slack chat footprint with Llama-3.1 via Groq... Please wait.\n")
            return chain.invoke({"text": content})
        except Exception as e:
            return f"An error occurred during summarization: {str(e)}"

async def main():
    # 1. Initialize analyzer engine
    analyzer = SlackAnalyzer()
    
    # Example Target User ID (Slack uses structural strings like U12345678 for profiles)
    target_user = "U0123456789" 
    
    # 2. Extract and summarize inside local RAM memory buffer
    analysis_result = await analyzer.run_analysis(user_slack_id=target_user)
    print("\n=== FINAL RESULT ===")
    print(analysis_result)
    
if __name__ == "__main__":
    asyncio.run(main())