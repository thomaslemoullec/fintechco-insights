# FinTechCo — Statements Service (Claude Code demo)

A small FastAPI payments/statements service used to demo **Claude Code's verification story**:
one Jira ticket, shipped safely, with problems caught at three layers (local review,
pre-commit gates, CI) before anything merges.

> ⚠️ **Demo repository.** The `demo-start` branch contains **intentional, planted security
> flaws** for the demo (see `SEEDS.md`). Do not deploy this. `main` is the fixed reference.

## 60-second quickstart
```bash
make setup        # venv + deps, register git hooks, seed the DB
make demo-check   # verify demo-ready (seeds present, control tests RED, tools + MCP)
make run          # http://127.0.0.1:8000  (try GET /accounts/1/transactions with header X-Customer-Id: 1)
make test         # full pytest suite
make reset        # restore to pristine demo-start
```
You also need `gitleaks` and `tfsec` on your PATH — see **SETUP.md**.

## What's here
| Path | What |
|---|---|
| `app/` | FastAPI service — transaction search + statement export |
| `app/ledger/` | legacy, undocumented rounding module (real git history) |
| `infra/terraform/` | the statements GCS bucket (infra) |
| `tests/` | pytest incl. authorisation/compliance **control tests** |
| `.claude/` | the harness — `CLAUDE.md` conventions, settings, hooks, a read-only `compliance-reviewer` subagent, skills |
| `.github/workflows/ci.yml` | CI gate: tests + ruff + gitleaks + tfsec + semgrep + Claude security review |
| `jira/TICKET.md` | the ticket the demo opens on (offline reference copy) |
| `DEMO.md` / `SEEDS.md` / `SETUP.md` | presenter run-sheet · seed catalogue · manual setup |

## The three verification layers
1. **Local** — tests-first + an AI compliance reviewer.
2. **Pre-commit** — deterministic gates (`ruff`, `gitleaks`, `tfsec`).
3. **CI** — full suite + SAST + secret/IaC scans + Claude security review, branch-protected,
   human-approved.

Branches: **`demo-start`** = seeded starting point (present the demo from here); **`main`** =
finished, fixed reference (outage fallback). Full script in `DEMO.md`.
