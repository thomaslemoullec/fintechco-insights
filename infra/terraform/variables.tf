variable "project_id" {
  type        = string
  description = "GCP project for the statements service (demo: no real project required)."
  default     = "fintechco-demo"
}

variable "region" {
  type        = string
  description = "US region only (see CLAUDE.md)."
  default     = "us-central1"
}

variable "statements_service_sa" {
  type        = string
  description = "Email of the statements-service runtime identity."
  default     = "statements-service@fintechco-demo.iam.gserviceaccount.com"
}
