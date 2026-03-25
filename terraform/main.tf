# ─────────────────────────────────────────────────────────────
# DataOps Compass — GCP Cloud Run Deployment
# ─────────────────────────────────────────────────────────────
# Services deployed:
#   - Cloud Run       : Flask app (dataops_assistant)
#   - Cloud SQL       : PostgreSQL 13 (conversations + feedback)
#   - Artifact Registry: Docker image storage
#   - Secret Manager  : OpenAI key + DB password
# ─────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─────────────────────────────────────────────────────────────
# Artifact Registry
# ─────────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "app" {
  repository_id = "dataops-assistant"
  location      = var.region
  format        = "DOCKER"
  description   = "DataOps Compass Docker images"
}

locals {
  image_url = "${var.region}-docker.pkg.dev/${var.project_id}/dataops-assistant/app:${var.image_tag}"
}

# ─────────────────────────────────────────────────────────────
# VPC
# ─────────────────────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "dataops-compass-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_global_address" "private_ip" {
  name          = "dataops-compass-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}

# ─────────────────────────────────────────────────────────────
# Cloud SQL
# ─────────────────────────────────────────────────────────────

resource "google_sql_database_instance" "postgres" {
  name             = "dataops-compass-db"
  database_version = "POSTGRES_13"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "app_db" {
  name     = var.postgres_db
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.postgres_user
  instance = google_sql_database_instance.postgres.name
  password = var.postgres_password
}

# ─────────────────────────────────────────────────────────────
# Secret Manager
# ─────────────────────────────────────────────────────────────

resource "google_secret_manager_secret" "openai_key" {
  secret_id = "dataops-compass-openai-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openai_key" {
  secret      = google_secret_manager_secret.openai_key.id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "postgres_password" {
  secret_id = "dataops-compass-postgres-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "postgres_password" {
  secret      = google_secret_manager_secret.postgres_password.id
  secret_data = var.postgres_password
}

# ─────────────────────────────────────────────────────────────
# Service Account
# ─────────────────────────────────────────────────────────────

resource "google_service_account" "cloud_run_sa" {
  account_id   = "dataops-compass-sa"
  display_name = "DataOps Compass Cloud Run SA"
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# ─────────────────────────────────────────────────────────────
# Cloud Run
# ─────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "app" {
  name     = "dataops-compass"
  location = var.region

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image = local.image_url

      ports {
        container_port = 5000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "POSTGRES_HOST"
        value = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }
      env {
        name  = "POSTGRES_DB"
        value = var.postgres_db
      }
      env {
        name  = "POSTGRES_USER"
        value = var.postgres_user
      }
      env {
        name  = "QDRANT_HOST"
        value = var.qdrant_host
      }
      env {
        name  = "QDRANT_PORT"
        value = tostring(var.qdrant_port)
      }
      env {
        name  = "COLLECTION_NAME"
        value = var.collection_name
      }
      env {
        name  = "MODEL_NAME"
        value = var.model_name
      }
      env {
        name  = "TZ"
        value = "Europe/Paris"
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "POSTGRES_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  depends_on = [
    google_service_networking_connection.private_vpc,
    google_secret_manager_secret_version.openai_key,
    google_secret_manager_secret_version.postgres_password,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
