import os

from typing import TypedDict
from typing import List
from typing import Dict

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END

load_dotenv()

class InterviewState(TypedDict):

    github_summary: str

    answer: str

    question: str

    history: List[Dict]


def interviewer_node(state: InterviewState):

    history_text = ""

    for item in state["history"]:

        history_text += (
            f"Question: {item['question']}\n"
        )

        history_text += (
            f"Answer: {item['answer']}\n\n"
        )

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7
    )

    prompt = ChatPromptTemplate.from_template(
        """
    You are a newly joined software engineer having a casual knowledge-transfer
    conversation with a senior engineer who is leaving the team.

    You are NOT conducting a job interview. You are having a natural,
    curiosity-driven conversation to understand the codebase deeply.

    RULES:
    - Ask exactly ONE question per turn.
    - Sound human and conversational. No robotic phrasing.
    - Your question MUST be about a DIFFERENT topic than any previous question.
    - If there is a previous answer, reference it specifically and go deeper or pivot.
    - Never repeat a question or rephrase the same topic.

    TOPICS TO COVER (pick the one least covered so far):
    - Architecture and system design decisions
    - Why specific frameworks or libraries were chosen
    - Deployment and infrastructure details
    - Database design and data flow
    - Known bugs, tech debt, or things the engineer would do differently
    - Error handling and edge cases
    - Third-party integrations and API design
    - Testing strategy and CI/CD
    - Performance bottlenecks and scaling
    - Anything the engineer is proud of or frustrated by

    KNOWLEDGE DOCUMENT:
    {summary}

    CONVERSATION HISTORY (questions already asked — do NOT repeat these topics):
    {history}

    LATEST ANSWER FROM ENGINEER:
    {answer}

    Generate your NEXT question. Pick a topic NOT yet covered above.
    """
    )
    
    chain = prompt | llm

    result = chain.invoke(
        {
            "summary": state["github_summary"],
            "history": history_text,
            "answer": state["answer"]
        }
    )

    content = result.content
    if isinstance(content, list):
        content = content[0].get("text", str(content))

    return {
        "question": content
    }


workflow = StateGraph(InterviewState)

workflow.add_node("interviewer",interviewer_node)

workflow.add_edge(START,"interviewer")

workflow.add_edge("interviewer",END)

interview_agent = workflow.compile()
