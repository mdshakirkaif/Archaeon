import os
import httpx
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio
from dotenv import load_dotenv
load_dotenv()

class GitHubAnalyzer:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.token}", 
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"

    async def _get_repos(self, org: str = None) -> list:
        if not self.token:
            print("[WARNING] GITHUB_TOKEN not found. Using local fallback repositories.")
            return ["dummy-auth-service", "dummy-billing-pipeline"]
            
        url = f"{self.base_url}/orgs/{org}/repos" if org else f"{self.base_url}/user/repos"
        params = {"per_page": 100, "type": "owner"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    return [repo["full_name"] for repo in response.json()]
                else:
                    url_user = f"{self.base_url}/users/mdshakirkaif/repos"
                    res_user = await client.get(url_user, headers=self.headers)
                    return [repo["full_name"] for repo in res_user.json()] if res_user.status_code == 200 else []
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            return []

    async def run_analysis(self, username: str, org: str = None) -> dict:
        """Fetches engineering footprint and extracts AI summary entirely in-memory."""
        since_date = (datetime.now() - timedelta(days=180)).isoformat()
        repos = await self._get_repos(org)
        
        commit_density = {}
        all_commits = []
        
        print(f"Scanning {len(repos)} repositories for user '{username}' over the last 180 days...")
        
        for repo in repos:
            url = f"{self.base_url}/repos/{repo}/commits"
            params = {"author": username, "since": since_date, "per_page": 100}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    if response.status_code == 200:
                        commits = response.json()
                        if commits:
                            commit_density[repo] = len(commits)
                            for c in commits:
                                all_commits.append({
                                    "repo": repo,
                                    "message": c["commit"]["message"]
                                })
            except Exception as e:
                print(f"Skipping {repo}: {e}")
                
        top_services = sorted(commit_density, key=commit_density.get, reverse=True)[:3]
        commit_summary_text = f"{username} owns {', '.join(top_services) if top_services else 'no repositories'} with {len(all_commits)} commits in the last 6 months."
        
        # Format strings for the Groq LLM
        commit_logs = [f"Repo: {c['repo']} | Msg: {c['message']}" for c in all_commits]
        input_text = f"Summary Data: {commit_summary_text}\n\nLogs:\n" + "\n".join(commit_logs[:50])
        
        # Run Groq Llama Summary
        ai_summary = self._generate_groq_summary(input_text)
        
        return {
            "github_username": username,
            "services": top_services,
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
                "You are Archaeon's expert engineering analyst. Summarize the raw GitHub history "
                "of a departing engineer. Identify core components, dependencies, "
                "and list out technical elements or fragile areas an AI interviewer should ask them about.\n\n"
                "Format output in markdown with concise bullet points."
            )),
            ("user", "Please summarize the technical footprint from this raw data:\n\n{text}")
        ])

        chain = prompt_template | llm | StrOutputParser()

        try:
            print("\nAnalyzing git footprint with Llama-3.1 via Groq... Please wait.\n")
            # print(chain.invoke({"text": content}))
            return chain.invoke({"text": content})
        except Exception as e:
            return f"An error occurred during summarization: {str(e)}"
async def main():
    # 1. Initialize analyzer engine
    analyzer = GitHubAnalyzer()
    target_user = "mdshakirkaif"
    
    # 2. Extract and summarize inside local RAM memory buffer
    analysis_result = await analyzer.run_analysis(username=target_user)
    print(analysis_result)
    
if __name__ == "__main__":
    asyncio.run(main())