variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "openai_api_key" {
  description = "OpenAI API key (stored in Secret Manager)"
  type        = string
  sensitive   = true
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "dataops_assistant"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "admin"
}

variable "postgres_password" {
  description = "PostgreSQL password (stored in Secret Manager)"
  type        = string
  sensitive   = true
}

variable "qdrant_host" {
  description = "Qdrant host"
  type        = string
  default     = "localhost"
}

variable "qdrant_port" {
  description = "Qdrant port"
  type        = number
  default     = 6333
}

variable "collection_name" {
  description = "Qdrant collection name"
  type        = string
  default     = "dataops_docs"
}

variable "model_name" {
  description = "OpenAI model to use"
  type        = string
  default     = "gpt-4o-mini"
}
