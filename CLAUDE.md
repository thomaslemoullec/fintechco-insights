# FinTechCo — Engineering Conventions (read every session)

This is the **Macro Insights** service at a regulated bank: it turns public economic data into
**client-facing research views**. Numbers shown here end up in front of clients, so the
conventions below are not style preferences — they are controls. Claude Code loads this file
every session and is expected to follow it.

## Data governance & provenance
- **Every external data pull is logged** — series/dataset id, row count, and the **as-of
  (vintage) date** — so any figure can be traced to its source. Never surface a number whose
  provenance you can't state.
- **Cite authoritative sources.** Each series carries its source (e.g. "U.S. BLS via FRED").
  Keep that metadata attached from ingestion through to the view.
- **Transformations are deterministic and documented.** Same input → same output. No hidden
  randomness in cleaning/analysis. Document the method (e.g. "YoY % change of the CPI index").
- **No look-ahead / no leakage.** Don't use data that wouldn't have been available at the
  point in time being analysed.

## Model risk & client-facing outputs
- Any client-facing view **must carry**: the **data as-of date**, the **source attribution**,
  a short **methodology note**, and a **disclaimer**. A figure without these is not shippable.
- **No unsupported claims.** Conclusions must follow from the data and the stated method.
- Analyses must be **reproducible** — a reviewer can re-run and get the same result.

## Secrets
- **No secrets in code.** API keys (e.g. `FRED_API_KEY`) and credentials come from the
  environment / Secret Manager, never hardcoded. Prefer Workload Identity Federation over
  long-lived keys.

## Data handling
- The service uses **public, non-personal** economic data only. Do not introduce customer or
  personal data into this service. Committed series data — real (cached from FRED) or
  synthetic fallback fixtures — must never contain customer or personal data.

## Cloud / region
- **US region only** for data at rest. Infra is Terraform under `infra/terraform/`.
- The dashboard deploys to **Cloud Run behind IAP** (identity-aware, **no public / `allUsers`
  access**) with least-privilege IAM. Nothing customer-facing is exposed to the open internet.

## Design system
- The UI **must follow the design system** in
  [`services/insights/web/DESIGN.md`](services/insights/web/DESIGN.md) — design tokens and
  components. Consistency across views is a control: client-facing output must look coherent
  and on-brand, not ad-hoc.

## Repo layout
- `services/<name>/` — one directory per service, each with its own `CLAUDE.md` for
  stack/layout/run/test specifics. Currently: `services/insights/`
  (see [`services/insights/CLAUDE.md`](services/insights/CLAUDE.md)).
- `infra/terraform/` — cloud infra, owned separately from any one service's app code.

## Shipping changes
- Never commit directly to `main`. "Create a PR" means: commit on a feature branch, push it,
  then open the PR against `main` — do this without being told each step.

## Definition of done
A change is done only when **tests pass + a reviewer has approved + security/IaC scans are
green**. Write tests first for anything that produces a **client-facing figure** or touches
**data provenance** — commit the tests before the implementation.
