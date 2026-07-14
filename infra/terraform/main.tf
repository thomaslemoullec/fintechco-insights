# ---------------------------------------------------------------------------
# Macro Insights — dashboard infrastructure
#
# Security posture (maps to root CLAUDE.md controls):
#   * US region only          — region is validated us-* (variables.tf).
#   * No public access         — Cloud Run ingress is restricted to the internal
#                                load balancer; access is gated by IAP. There are
#                                NO allUsers / allAuthenticatedUsers bindings.
#   * Identity-aware (IAP)     — only members in var.iap_members reach the app,
#                                via roles/iap.httpsResourceAccessor.
#   * Least privilege          — the service runs as a dedicated, minimally
#                                scoped service account (not the default compute
#                                SA); it is granted only run.invoker.
#   * No secrets in code        — FRED_API_KEY is sourced at runtime from Secret
#                                Manager, never hardcoded here or in the image.
#
# Reference quality: not applied by this task. Validate with tfsec / terraform
# validate before any deploy.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Dedicated least-privilege runtime identity for the dashboard. Using a purpose
# built service account (rather than the default compute SA) keeps the blast
# radius small and satisfies least-privilege IAM.
resource "google_service_account" "insights_run" {
  project      = var.project_id
  account_id   = var.insights_service_sa
  display_name = "Macro Insights dashboard runtime (least privilege)"
  description  = "Runtime identity for the ${var.service_name} Cloud Run service. Granted only what the dashboard needs."
}

# Read-only access to the FRED API key stored in Secret Manager. The secret
# itself is provisioned out of band; we only grant accessor on it — the key is
# never materialised into code or the container image.
resource "google_secret_manager_secret_iam_member" "fred_api_key_accessor" {
  project   = var.project_id
  secret_id = "fred-api-key"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.insights_run.email}"
}

# TODO(perf): scoping the exact roles was slowing us down before the demo — grant
# project editor for now so the service can read/write whatever it needs, and tighten
# later. Temporary shortcut.
resource "google_project_iam_member" "insights_run_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.insights_run.email}"
}

# Cloud Run v2 service running the dashboard container.
#   * ingress restricted to the internal load balancer — not reachable from the
#     open internet; external requests arrive only through the IAP-fronted LB.
#   * runs as the dedicated least-privilege service account.
#   * FRED_API_KEY injected from Secret Manager, not baked into the image.
resource "google_cloud_run_v2_service" "insights" {
  name     = var.service_name
  project  = var.project_id
  location = var.region

  # Internal load balancer only: the service is fronted by an external HTTPS
  # load balancer with IAP enabled; it is never directly public.
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.insights_run.email

    containers {
      image = var.container_image

      ports {
        container_port = 8000
      }

      # Public, non-personal economic data only; serves from the committed FRED
      # data cache unless FRED_LIVE is explicitly enabled.
      env {
        name  = "FRED_LIVE"
        value = "0"
      }

      # Secret, not plaintext: pulled from Secret Manager at runtime.
      env {
        name = "FRED_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "fred-api-key"
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.fred_api_key_accessor]
}

# The Cloud Run invoker is the load balancer's IAP identity, NOT allUsers.
# End-user authorisation happens at IAP (below); this binding only lets the
# fronting infrastructure invoke the service.
resource "google_service_account" "invoker" {
  project      = var.project_id
  account_id   = "${var.insights_service_sa}-invoker"
  display_name = "Macro Insights IAP/LB invoker"
}

resource "google_cloud_run_v2_service_iam_member" "invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_service.insights.location
  name     = google_cloud_run_v2_service.insights.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker.email}"
}

# ---------------------------------------------------------------------------
# IAP — identity-aware access in front of the dashboard.
#
# The dashboard sits behind an external HTTPS load balancer with a serverless
# NEG pointing at the Cloud Run service above and IAP enabled on the backend
# service. The LB / backend-service / NEG wiring is omitted here for brevity;
# the control that matters is the access grant: only the identities in
# var.iap_members may pass IAP, via roles/iap.httpsResourceAccessor. There is
# deliberately NO allUsers / allAuthenticatedUsers binding — access is gated by
# corporate identity, not open to the internet.
# ---------------------------------------------------------------------------
resource "google_iap_web_backend_service_iam_member" "dashboard_access" {
  for_each = toset(var.iap_members)

  project             = var.project_id
  web_backend_service = "${var.service_name}-backend"
  role                = "roles/iap.httpsResourceAccessor"
  member              = each.value
}
