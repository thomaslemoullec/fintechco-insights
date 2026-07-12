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

# CMEK for the statements bucket (AC2). Location "us" matches the bucket's "US"
# multi-region so the key can be used to encrypt objects in it.
resource "google_kms_key_ring" "statements" {
  name     = "statements-keyring"
  project  = var.project_id
  location = "us"
}

resource "google_kms_crypto_key" "statements" {
  name            = "statements-cmek"
  key_ring        = google_kms_key_ring.statements.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

# GCS's own service agent needs encrypt/decrypt on the key to use it as CMEK.
data "google_storage_project_service_account" "gcs" {
  project = var.project_id
}

resource "google_kms_crypto_key_iam_member" "gcs_can_use_statements_key" {
  crypto_key_id = google_kms_crypto_key.statements.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
}

# Bucket for exported customer statements. Statements contain NPI (see PAY ticket AC2).
resource "google_storage_bucket" "statements" {
  name                        = "fintechco-customer-statements"
  project                     = var.project_id
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = false

  encryption {
    default_kms_key_name = google_kms_crypto_key.statements.id
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Least privilege: only the statements-service runtime identity may read/write
# the bucket. No public or broad-authenticated-user bindings (AC2).
resource "google_storage_bucket_iam_member" "statements_service_read" {
  bucket = google_storage_bucket.statements.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.statements_service_sa}"
}

resource "google_storage_bucket_iam_member" "statements_service_write" {
  bucket = google_storage_bucket.statements.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${var.statements_service_sa}"
}
