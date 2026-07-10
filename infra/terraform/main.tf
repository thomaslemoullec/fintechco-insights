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

# CMEK for the statements bucket (AC2 — encryption at rest with a customer-managed key).
resource "google_kms_key_ring" "statements" {
  name     = "statements-keyring"
  location = "us"
  project  = var.project_id
}

resource "google_kms_crypto_key" "statements" {
  name            = "statements-cmek"
  key_ring        = google_kms_key_ring.statements.id
  rotation_period = "7776000s" # 90 days
}

# Bucket for exported customer statements. Statements contain NPI (see PAY ticket AC2).
resource "google_storage_bucket" "statements" {
  name                        = "fintechco-customer-statements"
  project                     = var.project_id
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = false

  # AC2: encrypt at rest with our customer-managed key.
  encryption {
    default_kms_key_name = google_kms_crypto_key.statements.id
  }
}

# AC2: least-privilege access — only the statements-service identity may read/write.
resource "google_storage_bucket_iam_member" "statements_service_rw" {
  bucket = google_storage_bucket.statements.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${var.statements_service_sa}"
}
