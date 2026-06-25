import os
from dotenv import load_dotenv
from retriever import retrieve_relevant_context
from generator import generate_grounded_answer

load_dotenv()

def main():
    print("Connecting to live Archaeon vector database...")
    print("Ready for queries. Type 'exit' to quit.\n")

    while True:
        prompt = input("Ask Archaeon: ")
        if prompt.strip().lower() in ["exit", "quit"]:
            break

        if not prompt.strip():
            continue

        print("\nSearching database tracks...")
        context = retrieve_relevant_context(prompt, k=2)

        if not context:
            print("No matching engineering context found in the database.\n")
            continue

        print("Analyzing codebase logic with Gemini...")
        reply = generate_grounded_answer(prompt, context)
        
        print(f"\nResponse:\n{reply}\n")
        print("=" * 40 + "\n")

if __name__ == "__main__":
    main()