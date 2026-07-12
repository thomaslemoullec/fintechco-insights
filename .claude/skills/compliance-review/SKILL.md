---
name: compliance-review
description: Run a compliance & security review of application and cloud changes against FinTechCo's banking controls, before commit. App + cloud checklist mapped to model risk (SR 11-7) / data governance / least privilege / CWE and the ticket's acceptance criteria. Use before committing changes to data pulls, client-facing figures, or Terraform.
---

# compliance-review

A checklist for reviewing changes to the Macro Insights service and its infra. Prefer
running the read-only `compliance-reviewer` subagent for an independent pass; use this
checklist directly for a quick self-review. Report findings in regulatory language and map
each to an acceptance criterion. **Complements** the deterministic scanners; does not
replace them.

## Application checklist (`services/insights/app/`)
- [ ] **Provenance & audit on every pull** — each external data pull logs series/dataset
      id, row count, and **as-of (vintage) date**. (Data governance)
- [ ] **Source attribution attached** — each series carries its source (e.g. "U.S. BLS via
      FRED"), kept from ingestion through to the view. (Data governance)
- [ ] **Deterministic transforms** — same input → same output; no hidden randomness;
      method documented. (Model risk · SR 11-7 · reproducibility)
- [ ] **No look-ahead / no leakage** — no data used that wasn't available at the point in
      time analysed. (Model risk)
- [ ] **Client-facing outputs carry the disclosure set** — data as-of date + source +
      methodology note + disclaimer on every figure/view. (Model risk · SR 11-7)
- [ ] **No secrets in code** — `FRED_API_KEY` / credentials from env or Secret Manager,
      not hardcoded. (CWE-798)
- [ ] **No personal data** — public, non-personal economic data only; fixtures synthetic.

## Cloud / Terraform checklist (`infra/terraform/`)
- [ ] **US region only** for data at rest / compute.
- [ ] **Cloud Run behind IAP** — identity-gated ingress; **no** public exposure, no
      `allUsers`/`allAuthenticatedUsers` bindings anywhere. (Least privilege · CWE-1188)
- [ ] **Least-privilege service account** — dedicated, minimally-scoped SA; not the
      default/compute SA. (Least privilege)
- [ ] **No committed service-account keys** — prefer Workload Identity Federation. (CWE-798)

## Output
For each gap: severity, file:line, the control + regulatory framing (model risk / SR 11-7,
data governance, least privilege) + CWE where one fits, the banking-terms impact, and a
one-line recommended fix. Finish with **BLOCK** or **PASS**.
