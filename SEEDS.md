# SEEDS.md — the deliberately planted flaws

These live **only** on `demo-start`. They are intentional. Do not "fix" them outside the
demo — your live prompting (Beats 7–9) is what fixes them. Each is marked `# DEMO-SEED`
in source. `main` holds the finished, fixed reference.

| # | Flaw | File : line | CWE / control | Violates | Caught in | Caught by |
|---|------|-------------|---------------|----------|-----------|-----------|
| 1 | **IDOR / BOLA** — endpoints serve/export any `account_id` with no ownership check | `app/transactions.py:54`, `:88` | CWE-639 · GLBA | **AC1** | Beat 5 (red test), Beat 7 (reviewer) | control test + `compliance-reviewer` |
| 2 | **NPI in logs** — full account number + customer name logged at INFO | `app/transactions.py:91` | CWE-532 · GLBA | **AC3** | Beat 5 (red test), Beat 7 | control test + reviewer |
| 3a | **No CMEK** on the statements bucket | `infra/terraform/main.tf:30` | GLBA encryption-at-rest | **AC2** | Beat 7, Beat 9/10 | `tfsec`, control test, reviewer |
| 3b | **Over-broad IAM** — `allUsers` read on a bucket holding NPI | `infra/terraform/main.tf:37` | least privilege | **AC2** | Beat 7, Beat 9/10 | `tfsec` (HIGH), control test, reviewer |
| 3c | **Exported SA key committed** | `infra/terraform/statements-exporter-sa-key.json` | CWE-798 | **AC2** | Beat 9 (pre-commit) | `gitleaks` |
| 4 | **Planted secret** — hardcoded `sk_live_…` signing key | `app/transactions.py:29` | CWE-798 | DoD (no secrets) | Beat 9 (pre-commit) | `gitleaks` (stripe-access-token) |

## Expected finding text (what the reviewer / scanners say)

- **Seed 1 (IDOR):** "Broken object-level authorization (CWE-639/BOLA): `account_id` is
  taken from the request path and never checked against the authenticated caller. Any
  customer can read or export another customer's transactions — a reportable GLBA data
  exposure. Violates AC1. Fix: verify ownership, else return 403."
- **Seed 2 (NPI in logs):** "Sensitive data in logs (CWE-532): the export handler logs the
  full account number and customer name at INFO. Statement data is NPI. Violates AC3. Fix:
  log a masked identifier (last 4) only."
- **Seed 3a (CMEK):** tfsec `google-storage-bucket-encryption-customer-key` — "Storage
  bucket encryption does not use a customer-managed key." Violates AC2.
- **Seed 3b (IAM):** tfsec `google-storage-no-public-access` (HIGH) — "Bucket allows public
  access" via `allUsers`. Violates AC2 (least privilege).
- **Seed 3c (SA key):** gitleaks `private-key` + `generic-api-key` in
  `statements-exporter-sa-key.json`.
- **Seed 4 (secret):** gitleaks `stripe-access-token` — `sk_live_…` in `app/transactions.py`.

## The fixes (Beats 8–9), for reference (already applied on `main`)
1. Add an ownership check in both handlers → `403` when `account.customer_id != caller`.
2. Replace the log line with a masked identifier (e.g. `****{last4}`), drop the name.
3. Terraform: add a CMEK `encryption { default_kms_key_name = ... }` block; replace the
   `allUsers` binding with a least-privilege `google_storage_bucket_iam_member` for the
   statements-service identity; delete the SA key file and use Workload Identity Federation.
4. Read the signing key from the environment / Secret Manager; remove the hardcoded value.

## Control tests that are RED on demo-start (Beat 5), GREEN after the fix
- `tests/test_transactions.py::test_customer_cannot_read_another_accounts_transactions`
- `tests/test_export.py::test_customer_cannot_export_another_accounts_statement`
- `tests/test_export.py::test_no_npi_in_logs`
- `tests/test_infra.py::test_statements_bucket_uses_cmek`
- `tests/test_infra.py::test_statements_bucket_is_not_public`
