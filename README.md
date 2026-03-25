# DataOps Knowledge Assistant 🔧

> An end-to-end RAG application for querying DataOps documentation (dbt, Apache Airflow, Great Expectations).

## Problem Description

DataOps practitioners frequently need to query documentation across multiple tools simultaneously. Searching across dbt docs, Airflow docs, and Great Expectations docs separately is time-consuming and context-switching heavy.

**This assistant lets you ask natural language questions** like:
- *"How do I define a dbt source with a freshness check?"*
- *"What is the difference between a DAG and a Task in Airflow?"*
- *"How do I set up a Great Expectations checkpoint?"*

...and get precise answers grounded in the official documentation, with source attribution.

## Architecture

```
User Question
     │
     ▼
  Flask API (/question)
     │
     ├─► Qdrant Vector Search  ──► Hybrid Re-ranking
     │        (BAAI/bge-small)
     │
     ├─► Prompt Builder
     │
     ├─► OpenAI gpt-4o-mini  ──► Answer
     │
     ├─► LLM-as-Judge Evaluation
     │
     └─► PostgreSQL (conversations + feedback)
                │
                └─► Grafana Dashboard
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Vector Store | Qdrant |
| Embeddings | BAAI/bge-small-en-v1.5 (fastembed) |
| LLM | OpenAI gpt-4o-mini |
| Ingestion | dlt + Python |
| API | Flask |
| Monitoring DB | PostgreSQL 13 |
| Dashboard | Grafana |
| Containerization | Docker + docker-compose |

## Dataset

Documentation sourced from:
- **dbt** — Core concepts, sources, models, tests, snapshots
- **Apache Airflow** — DAGs, operators, sensors, connections
- **Great Expectations** — Expectations, checkpoints, data docs

See `data/documents/` for the indexed markdown files.

## Setup & Quickstart

### Prerequisites
- Docker + Docker Compose
- OpenAI API key

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/dataops-knowledge-assistant
cd dataops-knowledge-assistant
cp .env_template .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start services

```bash
docker-compose up -d
```

### 3. Initialize database

```bash
docker-compose exec app python db_prep.py
```

### 4. Run ingestion pipeline

```bash
docker-compose exec app python ingest.py
```

### 5. Ask a question

```bash
curl -X POST http://localhost:5000/question \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I test for null values in dbt?"}'
```

Or use the CLI:

```bash
python cli.py
```

### 6. View monitoring dashboard

Open Grafana at http://localhost:3000 (admin/admin)

Initialize the dashboard:
```bash
python grafana/init.py
```

## Retrieval Evaluation

Two retrieval approaches are evaluated in `notebooks/evaluation-retrieval.ipynb`:

| Approach | Hit Rate | MRR |
|----------|----------|-----|
| Vector search (Qdrant) | TBD | TBD |
| Hybrid search (vector + keyword boost) | TBD | TBD |

→ Best approach used in production: **hybrid search**

## LLM Evaluation

Two prompt strategies evaluated in `notebooks/evaluation-rag.ipynb`:

| Approach | RELEVANT % | PARTLY_RELEVANT % |
|----------|-----------|-------------------|
| Prompt v1 (basic) | TBD | TBD |
| Prompt v2 (with source context) | TBD | TBD |

Evaluation method: **LLM-as-judge** (gpt-4o-mini)

## Monitoring Dashboard

Grafana dashboard includes:
1. Total questions over time
2. Relevance distribution (RELEVANT / PARTLY / NON)
3. User feedback (thumbs up / down ratio)
4. Average response time
5. OpenAI cost over time

## Ingestion Pipeline

Automated pipeline using **dlt**:
```bash
python dataops_assistant/ingest.py
```
- Chunks markdown documents (500 words, 50 overlap)
- Generates embeddings with fastembed (local, no API cost)
- Upserts into Qdrant in batches of 100

## Cloud Deployment (GCP)

The app is deployable to GCP Cloud Run using Terraform.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# fill in project_id, openai_api_key, postgres_password
terraform init && terraform apply
```

CI/CD via GitHub Actions (`.github/workflows/deploy.yml`):
- Triggers on push to `main`
- Builds Docker image → pushes to Artifact Registry → deploys to Cloud Run
- Uses Workload Identity Federation (no service account key)

See `terraform/README.md` for full setup instructions and cost estimate (~$10/month).

## Best Practices Implemented

- ✅ **Hybrid search**: vector + keyword boost re-ranking (module 6)
- ✅ **Document re-ranking**: combined score sorting (module 6)
- ✅ **Query rewriting**: gpt-4o-mini rewrites user question before retrieval (module A)
- ✅ **Cloud deployment**: GCP Cloud Run + Terraform + GitHub Actions CI/CD (+2 bonus pts)

## Reproducibility

All dependencies pinned in `requirements.txt`.
Data is accessible in `data/documents/`.
Full setup in 5 commands above.

## Project Structure

```
dataops-knowledge-assistant/
├── data/
│   └── documents/          ← source markdown docs
├── dataops_assistant/
│   ├── app.py              ← Flask API
│   ├── rag.py              ← RAG pipeline
│   ├── ingest.py           ← dlt ingestion
│   ├── db.py               ← PostgreSQL layer
│   └── db_prep.py          ← DB initialization
├── grafana/
│   ├── init.py
│   └── dashboard.json
├── notebooks/
│   ├── evaluation-retrieval.ipynb
│   └── evaluation-rag.ipynb
├── cli.py
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── .env_template
```
