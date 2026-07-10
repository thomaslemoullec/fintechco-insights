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

# Bucket for exported customer statements. Statements contain NPI (see PAY ticket AC2).
#
# DEMO-SEED 3a (no CMEK): this bucket has NO customer-managed encryption key. It falls
#   back to Google-managed keys. AC2 requires CMEK. tfsec flags this
#   (google-storage-bucket-encryption-customer-key). The fix adds an `encryption` block.
#
# DEMO-SEED 3b (over-broad IAM): the binding below grants read to `allUsers` — the
#   statements bucket is effectively PUBLIC. AC2 requires least privilege (only the
#   statements-service identity). tfsec flags this (google-storage-no-public-access).
resource "google_storage_bucket" "statements" {
  name                        = "fintechco-customer-statements"
  project                     = var.project_id
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = false

  # DEMO-SEED 3a: no CMEK key is configured on this bucket. Falls back to a
  #   Google-managed key, which does not satisfy AC2. The fix adds a CMEK encryption block.
}

# DEMO-SEED 3b: public/over-broad IAM binding on a bucket holding customer NPI.
resource "google_storage_bucket_iam_member" "statements_public_read" {
  bucket = google_storage_bucket.statements.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
