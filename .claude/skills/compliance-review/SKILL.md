---
name: compliance-review
description: Run a compliance & security review of application and cloud changes against FinTechCo's banking controls, before commit. App + cloud checklist mapped to GLBA / PCI / least privilege / CWE and the ticket's acceptance criteria. Use before committing changes to account data, logging, or Terraform.
---

# compliance-review

A checklist for reviewing changes to the statements service and its infra. Prefer running
the read-only `compliance-reviewer` subagent for an independent pass; use this checklist
directly for a quick self-review. Report findings in regulatory language and map each to an
acceptance criterion. **Complements** the deterministic scanners; does not replace them.

## Application checklist
- [ ] **Authorisation on every account access** — the `account_id` from the request is
      checked against the authenticated caller; unauthorised access returns `403`.
      (AC1 · GLBA · CWE-639 BOLA/IDOR)
- [ ] **Parameterised queries only** — no string-built SQL. (CWE-89)
- [ ] **No NPI in logs** — no full account numbers, customer names, or PANs; masked IDs
      only. (AC3 · GLBA · CWE-532)
- [ ] **No secrets in code** — credentials from env / Secret Manager, not hardcoded.
      (CWE-798)
- [ ] **Decimal money math** — integer cents / `Decimal`, never float.
- [ ] **Auditable** — each export records who / which account / when. (AC4)

## Cloud / Terraform checklist
- [ ] **CMEK** on buckets holding customer data (`default_kms_key_name`). (AC2 · GLBA)
- [ ] **Least privilege IAM** — no `allUsers`/`allAuthenticatedUsers`; only the
      statements-service identity can read/write. (AC2 · least privilege)
- [ ] **No committed service-account keys** — prefer Workload Identity Federation. (CWE-798)
- [ ] **US region only** for data at rest.

## Output
For each gap: severity, file:line, the control + CWE, the banking-terms impact, and a
one-line recommended fix. Finish with **BLOCK** or **PASS**.
