"""
Flask API for DataOps Knowledge Assistant.
Endpoints:
  POST /question   → ask a question, get RAG answer
  POST /feedback   → submit thumbs up/down feedback
  GET  /health     → healthcheck
"""

import uuid
from flask import Flask, request, jsonify

from rag import rag
import db

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/question", methods=["POST"])
def handle_question():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "No question provided"}), 400

    model = data.get("model", None)
    use_hybrid = data.get("use_hybrid", True)
    use_rewrite = data.get("use_rewrite", True)

    conversation_id = str(uuid.uuid4())

    kwargs = {"use_hybrid": use_hybrid, "use_rewrite": use_rewrite}
    if model:
        kwargs["model"] = model

    answer_data = rag(question, **kwargs)

    db.save_conversation(
        conversation_id=conversation_id,
        question=question,
        answer_data=answer_data,
    )

    return jsonify({
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer_data["answer"],
        "relevance": answer_data["relevance"],
        "search_type": answer_data["search_type"],
        "rewritten_query": answer_data.get("rewritten_query"),
        "response_time": round(answer_data["response_time"], 2),
    })


@app.route("/feedback", methods=["POST"])
def handle_feedback():
    data = request.json
    conversation_id = data.get("conversation_id")
    feedback = data.get("feedback")

    if not conversation_id or feedback not in [1, -1]:
        return jsonify({"error": "Invalid input. feedback must be 1 or -1"}), 400

    db.save_feedback(
        conversation_id=conversation_id,
        feedback=feedback,
    )

    return jsonify({
        "message": f"Feedback received for conversation {conversation_id}: {feedback}"
    })


@app.route("/stats", methods=["GET"])
def get_stats():
    feedback_stats = db.get_feedback_stats()
    relevance_stats = db.get_relevance_stats()
    return jsonify({
        "feedback": dict(feedback_stats) if feedback_stats else {},
        "relevance": [dict(r) for r in relevance_stats],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
