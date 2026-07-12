# FinTechCo — Engineering Conventions (read every session)

This is a **payments / customer-statements service** at a regulated bank. Money and
customer data flow through this code. The conventions below are not style preferences —
they are controls. Claude Code loads this file every session and is expected to follow it.

## Money
- **Never use floats for money.** Use `decimal.Decimal`, or store integer **cents** and
  convert at the edges. Rounding is `ROUND_HALF_EVEN` (banker's rounding).
- All monetary amounts in the DB are integer cents (`amount_cents`).

## Data access & authorisation
- **Authorisation is checked on every account access.** A caller may only read or export
  data for accounts they own. Never trust an `account_id` from the request as proof of
  ownership — check it against the authenticated caller's identity, then serve or `403`.
- **Parameterised queries only.** Never build SQL by string concatenation/f-strings.
- **Audit every financial-data read/export** (who, which account, when).

## Customer data / logging
- **Never log NPI or PANs.** No full account numbers, no customer names, no card numbers
  in logs — masked identifiers only (e.g. last 4, or a hashed account ref).
- Exported statements contain NPI: they must be **encrypted at rest with our CMEK** and
  stored least-privilege (only the statements-service identity can read/write the bucket).

## Secrets
- **No secrets in code.** Credentials come from the environment / Secret Manager, never
  hardcoded. Prefer Workload Identity Federation over long-lived service-account keys.

## Cloud / region
- **US region only** for data at rest.
- Infra is Terraform under `infra/terraform/`. Buckets holding customer data require CMEK
  and least-privilege IAM. No public or `allUsers`/`allAuthenticatedUsers` bindings.

## Repo layout
- `services/<name>/` — one directory per service, each with its own `CLAUDE.md` for
  stack/layout/run/test specifics. This repo currently has one: `services/statements/`
  (see [`services/statements/CLAUDE.md`](services/statements/CLAUDE.md)).
- `infra/terraform/` — cloud infra, shared across services, owned separately from any one
  service's app code.

## Definition of done
A change is done only when **tests pass + a reviewer has approved + security/IaC scans are
green** (lint, secret scan, tfsec/checkov, SAST). Write tests first for anything touching
authorisation or customer data. Commit tests before implementation.
