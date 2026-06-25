import os

from typing import TypedDict
from typing import List
from typing import Dict

from dotenv import load_dotenv

from langchain_groq import ChatGroq
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

    llm = ChatGroq(
        model=os.getenv(
            "GROQ_INTERVIEW_MODEL",
            "llama-3.1-8b-instant"
        ),
        temperature=0.7
    )

    prompt = ChatPromptTemplate.from_template(
        """
    ```

    You are a newly joined software engineer.

    You received a knowledge transfer document.

    Your job is to deeply understand the codebase.

    You are NOT conducting a job interview.

    You are talking to a senior engineer who is leaving.

    Ask only ONE question.

    Rules:

    * Sound human.
    * Be curious.
    * Ask follow-up questions.
    * Reference previous answers.
    * Ask about architecture.
    * Ask about tradeoffs.
    * Ask about decisions.
    * Ask about deployment.
    * Ask about failures.
    * Ask about scaling.

    Knowledge Transfer Document:

    {summary}

    Conversation History:

    {history}

    Latest Answer:

    {answer}

    Generate ONE realistic question.
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

    return {
        "question": result.content
    }


workflow = StateGraph(InterviewState)

workflow.add_node("interviewer",interviewer_node)

workflow.add_edge(START,"interviewer")

workflow.add_edge("interviewer",END)

interview_agent = workflow.compile()
