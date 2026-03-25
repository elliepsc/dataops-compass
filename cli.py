"""
CLI interface for DataOps Knowledge Assistant.
Usage:
  python cli.py
  python cli.py --question "How do I define a dbt source?"
"""

import argparse
import requests

BASE_URL = "http://localhost:5000"


def ask_question(question: str, use_hybrid: bool = True) -> dict:
    response = requests.post(
        f"{BASE_URL}/question",
        json={"question": question, "use_hybrid": use_hybrid},
    )
    return response.json()


def send_feedback(conversation_id: str, feedback: int):
    response = requests.post(
        f"{BASE_URL}/feedback",
        json={"conversation_id": conversation_id, "feedback": feedback},
    )
    return response.json()


def interactive_mode():
    print("DataOps Knowledge Assistant — CLI")
    print("Ask questions about dbt, Airflow, and Great Expectations.")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        print("Thinking...")
        result = ask_question(question)

        print(f"\nAssistant: {result['answer']}")
        print(f"[Relevance: {result.get('relevance', 'N/A')} | "
              f"Search: {result.get('search_type', 'N/A')} | "
              f"Time: {result.get('response_time', 0):.2f}s]\n")

        feedback_input = input("Helpful? [y/n/skip]: ").strip().lower()
        if feedback_input == "y":
            send_feedback(result["conversation_id"], 1)
            print("Thanks for the feedback!")
        elif feedback_input == "n":
            send_feedback(result["conversation_id"], -1)
            print("Thanks for the feedback!")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DataOps Knowledge Assistant CLI")
    parser.add_argument("--question", "-q", type=str, help="Ask a single question")
    parser.add_argument(
        "--no-hybrid", action="store_true", help="Use vector search only"
    )
    args = parser.parse_args()

    if args.question:
        result = ask_question(args.question, use_hybrid=not args.no_hybrid)
        print(f"Answer: {result['answer']}")
        print(f"Relevance: {result.get('relevance')}")
    else:
        interactive_mode()
