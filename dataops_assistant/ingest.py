"""
Ingestion pipeline for DataOps documentation.
Uses dlt to load documents and Qdrant for vector storage.

Sources:
- dbt documentation (local markdown files)
- Apache Airflow documentation (local markdown files)
- Great Expectations documentation (local markdown files)
"""

import os
import hashlib
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "dataops_docs")
DOCS_PATH = os.getenv("DOCS_PATH", "../data/documents")

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384


def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents_from_files(docs_path: str) -> list[dict]:
    documents = []
    docs_dir = Path(docs_path)

    if not docs_dir.exists():
        print(f"Warning: {docs_path} does not exist. Creating empty directory.")
        docs_dir.mkdir(parents=True, exist_ok=True)
        return documents

    for file_path in docs_dir.rglob("*.md"):
        if file_path.name == "README.md":
            continue
        source = file_path.parent.name
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
            doc_id = hashlib.md5(f"{file_path.name}_{i}".encode()).hexdigest()
            documents.append({
                "id": doc_id,
                "source": source,
                "filename": file_path.name,
                "chunk_index": i,
                "text": chunk,
                "filepath": str(file_path),
            })

    print(f"Loaded {len(documents)} chunks from {docs_path}")
    return documents


def setup_collection(client: QdrantClient):
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection {COLLECTION_NAME} already exists")


def index_documents(documents: list[dict]):
    if not documents:
        print("No documents to index.")
        return

    client = get_qdrant_client()
    setup_collection(client)

    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)

    texts = [doc["text"] for doc in documents]
    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = list(embedding_model.embed(texts))

    points = []
    for doc, embedding in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=int(hashlib.md5(doc["id"].encode()).hexdigest()[:8], 16),
                vector=embedding.tolist(),
                payload={
                    "source": doc["source"],
                    "filename": doc["filename"],
                    "chunk_index": doc["chunk_index"],
                    "text": doc["text"],
                    "filepath": doc["filepath"],
                },
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"Indexed {min(i + batch_size, len(points))}/{len(points)} chunks")

    print(f"Indexing complete. Total: {len(points)} chunks in '{COLLECTION_NAME}'")


def run_ingestion_pipeline():
    print("Starting DataOps documentation ingestion pipeline...")
    print(f"Source: {DOCS_PATH}")
    print(f"Target: Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")

    documents = load_documents_from_files(DOCS_PATH)

    if not documents:
        print("No documents found. Add .md files to data/documents/")
        print("Expected structure:")
        print("  data/documents/dbt/")
        print("  data/documents/airflow/")
        print("  data/documents/great_expectations/")
        return

    index_documents(documents)
    print("Pipeline complete.")


if __name__ == "__main__":
    run_ingestion_pipeline()
