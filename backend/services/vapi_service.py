import os
import asyncio
import httpx
import sys
from dotenv import load_dotenv

# Dynamically add the root 'Archaeon' directory to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import the standalone module class we refactored earlier
from connectors.github_analysis import GitHubAnalyzer

load_dotenv()

async def trigger_vapi_interview(analysis_result: dict):
    """Takes the in-memory analysis dict and provisions the Vapi agent session."""
    vapi_api_key = os.getenv("VAPI_API_KEY")
    if not vapi_api_key:
        print("❌ [ERROR] VAPI_API_KEY missing from environment.")
        return

    github_username = analysis_result["github_username"]
    services = analysis_result["services"]
    ai_summary = analysis_result["ai_summary"]

    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }
    
    dynamic_instruction = (
        f"You are Archaeon, an expert automated engineering offboarding interviewer. "
        f"You are speaking to senior software engineer: {github_username}.\n\n"
        f"Here is a technical summary of their code footprint extracted via Groq analytics:\n{ai_summary}\n\n"
        f"Your goal is to cross-examine them about these specific systems. Ask deep, technical, open-ended "
        f"questions about why things were built this way, what systems are fragile, and where hidden bugs reside. "
        f"Ask one concise question at a time. Be conversational but thoroughly analytical."
    )

    payload = {
        "assistant": {
            "name": "Archaeon Realtime Ingestion Agent",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{"role": "system", "content": dynamic_instruction}]
            },
            "voice": "jennifer-playht",
            "firstMessage": f"Hello, I am Archaeon. I've been reviewing your contributions to {services[0] if services else 'the architecture'} over the last six months. Let's talk about the key technical decisions you made there. What was the most complex trade-off you had to implement?"
        }
    }

    print(f"Initializing Vapi Voice Agent session for engineer '{github_username}'...")
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.vapi.ai/assistance", json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print("\n🚀 [SUCCESS] Vapi Voice Agent Session successfully initialized!")
            print("Response payload returned successfully.")
        else:
            print(f"\n❌ [VAPI ERROR] Call initialization failed: {response.text}")

async def main():
    # 1. Initialize analyzer engine
    analyzer = GitHubAnalyzer()
    target_user = "mdshakirkaif"
    
    # 2. Extract and summarize inside local RAM memory buffer
    analysis_result = await analyzer.run_analysis(username=target_user)
    
    # 3. Pass data object directly to the voice session pipeline
    await trigger_vapi_interview(analysis_result)
    
    # 4. FUTURE DATABASE HOOK PLACEHOLDER
    # You can easily add your db execution lines here later:
    # await save_summary_to_postgres(analysis_result)
    # await map_nodes_to_neo4j(analysis_result)
    print("\n💡 Note: In-memory pipeline complete. Database storage hooks can be safely attached here later.")

if __name__ == "__main__":
    asyncio.run(main())