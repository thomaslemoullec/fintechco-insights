# services/insights — Macro Insights service

Bank-wide controls (data governance, model risk, secrets, region, design system, definition of
done) live in the root [`CLAUDE.md`](../../CLAUDE.md). This file covers only service specifics.

## Stack
- Python 3.11+ / FastAPI. One process serves the JSON API (`/api/*`) and the static dashboard
  UI (`/`).
- Data: economic series from FRED. Runs on committed **synthetic fixtures** until live API
  access is provisioned (`FRED_LIVE=1` + `FRED_API_KEY` switch on the real pull).

## Layout
- `app/main.py` — FastAPI entrypoint; mounts the API router and serves `web/`.
- `app/api.py` — HTTP endpoints (`/api/indicators`, `/api/series/{id}`, `/api/news`).
- `app/fred.py` — data source layer; key from env, provenance logging on every pull.
- `app/analysis.py` — cleaning / alignment / exploratory analysis (deterministic).
- `app/indicators.py` — indicator catalogue with source/units/frequency metadata.
- `app/data/*.csv` — synthetic FRED fixtures (committed; no real data).
- `web/` — static dashboard; design system documented in `web/DESIGN.md`.
- `tests/` — pytest, including `@pytest.mark.control` data-governance / model-risk tests.

## Run / test (from repo root, no `cd` needed)
- `make dev` — serve the app at http://127.0.0.1:8000
- `make test` — full suite · `make test-control` — control tests only
- `make seed` — regenerate the deterministic fixtures
