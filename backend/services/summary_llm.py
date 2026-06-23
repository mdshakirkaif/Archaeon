import os
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

def read_input_source(source):
    """Reads content from a file path or direct string input."""
    if os.path.exists(source):
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()
    return source

def generate_summary(content):
    """Analyzes the content type and generates a tailored summary."""
    # if not os.environ.get("GROQ_API_KEY"):
    #     return "Error: GROQ_API_KEY environment variable not set."

    # Initialize the LLM
    llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant",
    temperature=0.3,
    )

    # Dynamic prompt that adapts to Chats, Q&A, or GitHub/Code content
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert text analyzer. Your job is to summarize the provided text. "
            "First, identify the context (e.g., Git repository/Code, Q&A thread, Chat log, or general document). "
            "Then, provide a structured summary based on the format:\n\n"
            "- **For Chats:** Focus on the main topics discussed, key decisions made, and clear action items (with owners if mentioned).\n"
            "- **For Q&A:** State the core question/problem, the accepted or best solution, and any important alternative context.\n"
            "- **For Code/GitHub:** Explain what the code/repository does, its main components/functions, and dependencies.\n"
            "- **For General Text:** Provide a TL;DR and key bullet points.\n\n"
            "Keep the summary concise, actionable, and highly readable using markdown."
        )),
        ("user", "Please summarize the following content:\n\n{text}")
    ])

    # Create the chain
    chain = prompt_template | llm | StrOutputParser()

    try:
        print("Analyzing and summarizing content... Please wait.\n")
        response = chain.invoke({"text": content})
        print(response)
        return response
    except Exception as e:
        return f"An error occurred during summarization: {str(e)}"

if __name__ == "__main__":
    # Allows running via command line: python summary.py "path/to/file.txt" or "raw text"
    raw_content="Q: How do I revert a git commit? A: Use git reset --hard HEAD~1 if you want to destroy changes, or git revert <commit_id> to create a new commit that undoes the changes safely."
    
    summary = generate_summary(raw_content)
    
    print("=== SUMMARY ===")
    print(summary)