# Statements service — stack & layout

Bank-wide controls (money handling, authorisation, logging, secrets, region, definition of
done) live in the repo-root [`CLAUDE.md`](../../CLAUDE.md) and apply here too — this file
covers only what's specific to this service.

## Stack
- Python 3.11+ / FastAPI. SQLite (`services/statements/data/statements.db`) seeded with
  **fake** data only.

## Layout
- `app/` — the service (transaction search + statement export).
- `app/ledger/` — **legacy, owned elsewhere; do not modify as part of feature work.**
- `tests/` — pytest, including the authorisation/compliance control tests.
- `migrations/` — SQL schema.

## Run / test
From the repo root: `make run` serves the API; `make test` runs the full suite; `make
test-control` runs only the control tests. These targets already know where this service
lives — no need to `cd` into `services/statements/` first.
