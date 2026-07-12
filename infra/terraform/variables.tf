variable "project_id" {
  description = "GCP project that hosts the Macro Insights dashboard."
  type        = string
  default     = "fintechco-demo"
}

variable "region" {
  description = "Deployment region. US only — data at rest and compute must stay in a US region (root CLAUDE.md)."
  type        = string
  default     = "us-central1"

  validation {
    condition     = startswith(var.region, "us-")
    error_message = "region must be a US region (us-*): data at rest is US-only."
  }
}

variable "service_name" {
  description = "Cloud Run service name for the dashboard."
  type        = string
  default     = "macro-insights"
}

variable "insights_service_sa" {
  description = "Account id (local part, before the @) for the least-privilege runtime service account the dashboard runs as."
  type        = string
  default     = "macro-insights-run"
}

variable "container_image" {
  description = "Fully-qualified container image for the dashboard (e.g. us-docker.pkg.dev/<project>/<repo>/macro-insights:<tag>)."
  type        = string
  default     = "us-docker.pkg.dev/fintechco-demo/insights/macro-insights:latest"
}

variable "iap_members" {
  description = "Identities allowed through IAP to reach the dashboard, e.g. [\"group:macro-insights-users@fintechco.com\"]. Never allUsers/allAuthenticatedUsers."
  type        = list(string)
  default     = ["group:macro-insights-users@fintechco.com"]

  validation {
    condition = alltrue([
      for m in var.iap_members : m != "allUsers" && m != "allAuthenticatedUsers"
    ])
    error_message = "iap_members must not contain allUsers or allAuthenticatedUsers: the dashboard is identity-gated, never public."
  }
}
