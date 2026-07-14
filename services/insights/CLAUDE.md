# services/insights — Macro Insights service

Bank-wide controls (data governance, model risk, secrets, region, design system, definition of
done) live in the root [`CLAUDE.md`](../../CLAUDE.md). This file covers only service specifics.

## Stack
- Python 3.11+ / FastAPI. One process serves the JSON API (`/api/*`) and the static dashboard
  UI (`/`).
- Data: economic series from FRED, cached as committed CSVs in `app/data/`. `make fetch`
  (or `FRED_LIVE=1`) refreshes from the live API using `FRED_API_KEY` (from Secret Manager);
  `scripts/gen_fixtures.py` is an offline synthetic fallback.

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

## Adding a new dashboard view — reuse these, don't re-derive them
- Check `app/indicators.py` first — `INFLATION` (CPI YoY) and `UNRATE` are already catalogued
  with source/units/frequency. A new view combining existing indicators needs no new data pull.
- `web/assets/charts.js` `lineOption(series, indicator)` — reuse for any line/time-series chart.
- `web/assets/components.js` `viewMeta({ sources, methodology, disclaimer })` — renders the
  as-of/source/methodology/disclaimer footer required by the root CLAUDE.md. Call it with real
  values instead of hand-rolling a footer.
- `web/assets/app.js` — mirror the existing `renderMacro` + `renderChart` pattern for a new view;
  add one entry to the `ROUTES` table + one nav link, same as an existing view.
- No new API endpoint for a view combining existing indicators — `GET /api/series/{id}` already
  returns `as_of` + `points` per indicator; call it twice client-side and merge/align in the view.
- TDD control tests (the "write tests first" ones, per the root CLAUDE.md) go in
  `tests/test_analysis.py` under `@pytest.mark.control`; endpoint-level tests go in
  `tests/test_api.py`. Run `make test-control` for just the former.
