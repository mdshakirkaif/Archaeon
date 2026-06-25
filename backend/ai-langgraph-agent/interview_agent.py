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
    if state["history"]:
        for i, item in enumerate(state["history"], 1):
            history_text += (
                f"Q{i}: {item['question']}\n"
                f"A{i}: {item['answer']}\n\n"
            )
    else:
        history_text = "(No questions asked yet — this is the first question)\n"

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7
    )

    if not state["history"]:
        first_question_prompt = ChatPromptTemplate.from_template(
            """
    You are a newly joined software engineer starting a casual knowledge-transfer
    conversation with a senior engineer who is leaving the team.

    This is the VERY FIRST question. There is no conversation history yet.

    KNOWLEDGE DOCUMENT:
    {summary}

    Pick the MOST important or complex thing from the knowledge document and ask
    about it. This sets the tone for the whole conversation.

    Good first questions:
    - "I was looking at the codebase and noticed [specific thing]. Can you walk me through how that works?"
    - "What's the most critical part of this system that I need to understand?"
    - "I see [specific module/service]. What's the story behind building that?"

    Ask exactly ONE question. Sound human and conversational.
    """
        )
        chain = first_question_prompt | llm
        result = chain.invoke({"summary": state["github_summary"]})
    else:
        followup_prompt = ChatPromptTemplate.from_template(
            """
    You are a newly joined software engineer having a casual knowledge-transfer
    conversation with a senior engineer who is leaving the team.

    RULES:
    - Ask exactly ONE question.
    - Sound human and conversational.
    - Your question MUST be about a TOPIC NOT YET COVERED below.
    - Reference the engineer's latest answer specifically — go deeper or pivot.
    - NEVER ask about the same thing twice.

    TOPICS (check which are already covered, then pick one that is NOT):
    1. Architecture and system design
    2. Framework/library choices and why
    3. Deployment and infrastructure
    4. Database design and data flow
    5. Bugs, tech debt, or regrets
    6. Error handling and edge cases
    7. Third-party integrations and APIs
    8. Testing and CI/CD
    9. Performance bottlenecks and scaling
    10. Proudest achievement or biggest frustration

    PREVIOUS Q&A (numbered — identify which topics these cover):
    {history}

    LATEST ANSWER:
    {answer}

    Now ask about a DIFFERENT topic than any above. Pick the least-covered number.
    """
        )
        chain = followup_prompt | llm
        result = chain.invoke({
            "history": history_text,
            "answer": state["answer"]
        })

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
