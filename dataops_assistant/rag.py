"""
RAG pipeline for DataOps Knowledge Assistant.
Uses Qdrant for vector search and OpenAI for generation.
Includes LLM-as-judge evaluation inline.

Best practices implemented:
- Hybrid search (vector + keyword re-ranking)
- Document re-ranking by combined score
- Query rewriting for improved retrieval
"""

import os
import json
from time import time

from openai import OpenAI
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "dataops_docs")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
NUM_RESULTS = 5

openai_client = OpenAI()
embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)


def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# ──────────────────────────────────────────────
# SEARCH
# ──────────────────────────────────────────────

def vector_search(query: str, source_filter: str = None) -> list[dict]:
    """Search Qdrant using vector embeddings."""
    client = get_qdrant_client()
    query_vector = list(embedding_model.embed([query]))[0].tolist()

    search_filter = None
    if source_filter:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        search_filter = Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=source_filter))]
        )

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=NUM_RESULTS,
        query_filter=search_filter,
    )

    return [
        {
            "text": hit.payload["text"],
            "source": hit.payload["source"],
            "filename": hit.payload["filename"],
            "score": hit.score,
        }
        for hit in results
    ]


def hybrid_search(query: str, source_filter: str = None) -> list[dict]:
    """Hybrid search: vector + keyword re-ranking."""
    results = vector_search(query, source_filter)

    query_terms = set(query.lower().split())
    for result in results:
        text_terms = set(result["text"].lower().split())
        overlap = len(query_terms & text_terms)
        result["score"] = result["score"] + (overlap * 0.01)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:NUM_RESULTS]


# ──────────────────────────────────────────────
# PROMPT BUILDING
# ──────────────────────────────────────────────

PROMPT_TEMPLATE = """
You are a DataOps expert assistant. Answer the QUESTION using only the information from the CONTEXT below.
If the answer is not in the context, say "I don't have enough information to answer this question."
Always mention which tool (dbt/Airflow/Great Expectations) your answer refers to.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

ENTRY_TEMPLATE = """
[Source: {source} | File: {filename}]
{text}
""".strip()


def build_prompt(query: str, search_results: list[dict]) -> str:
    context = "\n\n".join(
        ENTRY_TEMPLATE.format(**doc) for doc in search_results
    )
    return PROMPT_TEMPLATE.format(question=query, context=context)


# ──────────────────────────────────────────────
# QUERY REWRITING
# ──────────────────────────────────────────────

REWRITE_PROMPT = """
You are an expert at improving search queries for a DataOps knowledge base
covering dbt, Apache Airflow, and Great Expectations.

Rewrite the following question to improve retrieval accuracy:
- Make it more specific and keyword-rich
- Expand abbreviations (e.g. "GE" → "Great Expectations")
- Add relevant technical terms the user might not have used
- Keep it as a question

Original question: {question}

Rewritten question (return only the rewritten question, nothing else):
""".strip()


def rewrite_query(query: str) -> str:
    """Rewrite user query to improve retrieval. Best practice: query rewriting."""
    prompt = REWRITE_PROMPT.format(question=query)
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()


# ──────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────

def llm(prompt: str, model: str = MODEL_NAME) -> tuple[str, dict]:
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content
    token_stats = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return answer, token_stats


# ──────────────────────────────────────────────
# EVALUATION (LLM-as-judge)
# ──────────────────────────────────────────────

EVALUATION_PROMPT = """
You are an expert evaluator for a RAG system about DataOps tools (dbt, Airflow, Great Expectations).
Analyze the relevance of the generated answer to the given question.
Classify as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Question: {question}
Generated Answer: {answer}

Respond with parsable JSON only, no code blocks:
{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[brief explanation]"
}}
""".strip()


def evaluate_relevance(question: str, answer: str) -> tuple[dict, dict]:
    prompt = EVALUATION_PROMPT.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt, model="gpt-4o-mini")
    try:
        return json.loads(evaluation), tokens
    except json.JSONDecodeError:
        return {"Relevance": "UNKNOWN", "Explanation": "Parse failed"}, tokens


def calculate_openai_cost(model: str, tokens: dict) -> float:
    if model == "gpt-4o-mini":
        return (
            tokens["prompt_tokens"] * 0.00015
            + tokens["completion_tokens"] * 0.0006
        ) / 1000
    elif model == "gpt-4o":
        return (
            tokens["prompt_tokens"] * 0.005
            + tokens["completion_tokens"] * 0.015
        ) / 1000
    return 0.0


# ──────────────────────────────────────────────
# MAIN RAG FUNCTION
# ──────────────────────────────────────────────

def rag(
    query: str,
    model: str = MODEL_NAME,
    use_hybrid: bool = True,
    use_rewrite: bool = True,
) -> dict:
    t0 = time()

    # 1. Query rewriting
    rewritten_query = rewrite_query(query) if use_rewrite else query

    # 2. Search with rewritten query
    search_results = (
        hybrid_search(rewritten_query) if use_hybrid else vector_search(rewritten_query)
    )

    # 3. Generate with original query + retrieved context
    prompt = build_prompt(query, search_results)
    answer, token_stats = llm(prompt, model=model)

    # 4. Evaluate relevance
    relevance, rel_token_stats = evaluate_relevance(query, answer)

    took = time() - t0
    openai_cost = (
        calculate_openai_cost(model, token_stats)
        + calculate_openai_cost("gpt-4o-mini", rel_token_stats)
    )

    return {
        "answer": answer,
        "model_used": model,
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get("Explanation", ""),
        "search_type": "hybrid" if use_hybrid else "vector",
        "rewritten_query": rewritten_query if use_rewrite else None,
        "sources": [r["source"] for r in search_results],
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_completion_tokens": rel_token_stats["completion_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
        "openai_cost": openai_cost,
    }
