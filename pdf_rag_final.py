import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from rag_engine import ask_question, stream_question, rewrite_query

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    print("🤖 PDF RAG Assistant (Document-Agnostic Core)")
    print("Ask questions about your ingested PDFs.")
    print("Type 'exit' to quit.\n")

    messages = []

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() == "exit":
            print("Goodbye!")
            break

        res = ask_question(query, messages, return_details=True)

        print(f"\nAI: {res['answer']}\n")

        print("Sources:")
        if res.get("sources"):
            for s in res["sources"]:
                print(f"- {s['source']} — Page {s['page']}")
        else:
            print("- None")
        print()

        # Update session messages
        messages.append({"role": "user", "content": query})
        messages.append({"role": "assistant", "content": res["answer"]})


if __name__ == "__main__":
    main()