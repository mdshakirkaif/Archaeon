import os
from google import genai
from google.genai import types
import config

def generate_grounded_answer(query, retrieved_docs):
    if not os.getenv("GEMINI_API_KEY"):
        print("Configuration Error: GEMINI_API_KEY environment variable is missing.")
        return "Error: Missing API Key"

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    context_blocks = []
    for i, doc in enumerate(retrieved_docs):
        source_name = doc.metadata.get("source", f"Document_{i+1}")
        context_blocks.append(f"--- START SOURCE {i+1}: {source_name} ---\n{doc.page_content}\n--- END SOURCE {i+1} ---")
    
    context_text = "\n\n".join(context_blocks)

    system_instruction = (
        "You are Archaeon, an elite software architecture and codebase intelligence system. "
        "Your purpose is to preserve tribal knowledge, engineering decisions, and technical context "
        "retrieved from offboarding interviews, pull requests, Slack logs, and documentation.\n\n"
        
        "CRITICAL INSTRUCTIONS:\n"
        "1. Answer the user's question using ONLY the provided architectural context snippets.\n"
        "2. Be technically precise, concise, and direct. Avoid generic fluff.\n"
        "3. Explicitly cite your sources inline using [Source X] notation when referencing a piece of knowledge.\n"
        "4. If the provided context does not contain the answer or logical grounds to deduce it, state exactly: "
        "'I cannot find the context for this engineering decision in Archaeon's knowledge base.'"
    )

    contents = f"Retrieved Context:\n{context_text}\n\nUser Engineering Query: {query}"

    response = client.models.generate_content(
        model=config.LLM_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1
        )
    )

    return response.text