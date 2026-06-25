import os
import requests
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def fetch_profile(username: str):

    url = f"https://api.github.com/users/{username}"

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("Failed to fetch GitHub profile")

    return response.json()


def fetch_repositories(token: str):

    headers = {
        "Authorization": f"token {token}"
    }

    url = "https://api.github.com/user/repos?per_page=100&type=owner"

    response = requests.get(
        url,
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(
            f"GitHub Error: {response.text}"
        )

    return response.json()


def fetch_readme(token, full_name):

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.raw"
    }

    url = f"https://api.github.com/repos/{full_name}/readme"

    response = requests.get(
        url,
        headers=headers
    )

    if response.status_code == 200:
        return response.text[:5000]

    return "README not available."


def build_master_document(profile,repositories,token):

    document = []

    document.append(
        f"Developer Name: {profile.get('name')}"
    )

    document.append(
        f"GitHub Username: {profile.get('login')}"
    )

    document.append(
        f"Bio: {profile.get('bio')}"
    )

    document.append(
        f"Public Repositories: {profile.get('public_repos')}"
    )

    document.append("\n")

    for repo in repositories:

        readme = fetch_readme(
            token,
            repo["full_name"]
        )

        document.append(
            "=" * 100
        )

        document.append(
            f"Repository: {repo['name']}"
        )

        document.append(
            f"Description: {repo.get('description')}"
        )

        document.append(
            f"Language: {repo.get('language')}"
        )

        document.append(
            f"Stars: {repo.get('stargazers_count')}"
        )

        document.append(
            f"Topics: {repo.get('topics', [])}"
        )

        document.append(
            f"README:\n{readme}"
        )

        document.append("\n")

    return "\n".join(document)

def generate_knowledge_summary(master_document):
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )

    prompt = ChatPromptTemplate.from_template(
        """
    ```

    You are a senior software architect.

    Analyze this GitHub profile.

    Create an EXTREMELY DETAILED knowledge transfer document.

    Requirements:

    * Cover every repository.
    * Mention architecture.
    * Mention frameworks.
    * Mention APIs.
    * Mention databases.
    * Mention deployment strategy.
    * Mention patterns used.
    * Mention relationships between projects.
    * Mention reusable components.
    * Mention technical decisions.

    The output should be very detailed.

    GitHub Data:

    {github_data}
    """
    )


    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "github_data": master_document
    })

    if isinstance(result, list):
        return result[0].get("text", str(result))
    return result


def analyze_github(username, token, selected_repos=None):
    profile = fetch_profile(username)

    all_repos = fetch_repositories(token)

    if selected_repos:
        repos = [r for r in all_repos if r["name"] in selected_repos]
    else:
        repos = all_repos

    master_document = build_master_document(
        profile,
        repos,
        token
    )

    knowledge_summary = generate_knowledge_summary(
        master_document
    )

    return {
        "profile": profile,
        "repos": repos,
        "master_document": master_document,
        "knowledge_summary": knowledge_summary
    }

