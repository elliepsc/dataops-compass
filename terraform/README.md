# Cloud Deployment — GCP Cloud Run

Deploy the DataOps Knowledge Assistant to GCP using Terraform.

## Architecture

```
Internet
   │
   ▼
Cloud Run (Flask app)
   │            │
   ▼            ▼
Cloud SQL    Qdrant (external)
(PostgreSQL)
   │
   ▼
Grafana (local or separate deploy)
```

> **Note on Qdrant**: GCP does not have a managed Qdrant service.
> Options: (1) run Qdrant on a GCE VM, (2) use Qdrant Cloud free tier,
> (3) use a Cloud Run sidecar. This config defaults to Qdrant Cloud.

## Prerequisites

### 1. Enable GCP APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  servicenetworking.googleapis.com \
  --project YOUR_PROJECT_ID
```

### 2. Configure authentication (WIF recommended)

```bash
# Option A: Workload Identity Federation (recommended, no key file)
# See: https://cloud.google.com/iam/docs/workload-identity-federation

# Option B: Service account key (dev only)
gcloud auth application-default login
```

## Deploy steps

### Step 1 — Build and push Docker image

```bash
# Authenticate Docker to Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Build image
docker build -t europe-west1-docker.pkg.dev/YOUR_PROJECT/dataops-assistant/app:latest .

# Push image
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT/dataops-assistant/app:latest
```

### Step 2 — Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### Step 3 — Deploy infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### Step 4 — Initialize database on Cloud Run

```bash
# Get Cloud Run URL from terraform output
export APP_URL=$(terraform output -raw cloud_run_url)

# Init DB (runs db_prep.py via Cloud Run job or manually)
curl -X POST $APP_URL/health
```

### Step 5 — Run ingestion pipeline

```bash
# From local machine with documents in data/documents/
# Point QDRANT_HOST to your Qdrant Cloud instance
QDRANT_HOST=your-qdrant-cloud-host python dataops_assistant/ingest.py
```

### Step 6 — Test the deployed API

```bash
export APP_URL=$(terraform output -raw cloud_run_url)

curl -X POST $APP_URL/question \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I define a dbt source?"}'
```

## Tear down

```bash
terraform destroy
```

## Cost estimate

| Service | Tier | Est. cost/month |
|---------|------|----------------|
| Cloud Run | 0 → 2 instances | ~$0 (free tier) |
| Cloud SQL | db-f1-micro | ~$10 |
| Artifact Registry | <1GB | ~$0.10 |
| Secret Manager | <10k ops | ~$0 |
| **Total** | | **~$10/month** |

> Cloud Run scales to zero when not in use — cost is minimal for a portfolio project.
