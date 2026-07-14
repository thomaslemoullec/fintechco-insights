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
- `app/data/*.csv` — cached FRED series data (real, public; committed for reproducibility).
- `web/` — static dashboard; design system documented in `web/DESIGN.md`.
- `tests/` — pytest, including `@pytest.mark.control` data-governance / model-risk tests.

## Run / test (from repo root, no `cd` needed)
- `make dev` — serve the app at http://127.0.0.1:8000
- `make test` — full suite · `make test-control` — control tests only
- `make seed` — regenerate the deterministic fixtures

## Adding a new dashboard view — reuse these, don't re-derive them
This map is kept accurate as the source of truth for planning — trust its claims about what
already exists rather than re-reading every referenced file to double-check them; open a file
only when you need its exact current syntax to write against it.

- **"A new tab" means a segmented toggle within the existing page, not a new sidebar route** —
  e.g. an "Inflation vs. Unemployment" tab lands as a second `segmented` option inside
  `renderMacro`'s existing `#/indicators/macro` route, alongside the current indicator-cards
  view. Don't add a new top-level `ROUTES` entry or sidebar nav link unless the ticket
  explicitly asks for a new page.
- Check `app/indicators.py` first — `INFLATION` (CPI YoY) and `UNRATE` are already catalogued
  with source/units/frequency. A new view combining existing indicators needs no new data pull.
- `app/analysis.py` `build_frame()` already aligns inflation/unemployment (and fed funds) onto
  one monthly index and drops unpaired months — this is the pairing logic a two-series view
  needs; don't re-derive it. `series_view()` already returns `disclaimer` (from the
  module-level `DISCLAIMER` constant) alongside `as_of`/`source`/`points`.
- **For a view needing both series paired in one payload** (e.g. inflation vs. unemployment),
  add one thin endpoint in `app/api.py` over `analysis.build_frame()` rather than joining two
  `/api/series/{id}` calls client-side — the control test for exactly this is **already
  written** at `tests/test_api.py::test_inflation_unemployment_view` (currently red — run
  `make test-control` to see it fail, then implement `GET /api/views/inflation-unemployment`
  to turn it green). It should return `{as_of, disclaimer, points: [{date, inflation,
  unemployment}, ...]}`, built from `build_frame()`'s `inflation`/`unemployment` columns.
- `web/assets/charts.js` `lineOption(series, indicator)` — reuse as-is for a single-series chart.
  For a two-series chart, add a sibling exported function, same shape as `lineOption`, reusing
  `THEME`, `axisCommon`, `tooltipCommon`, `fmtMonth` — don't rebuild these. Ready-to-adapt
  starting point:
  ```js
  export function twoSeriesOption(dates, seriesA, seriesB, labelA, labelB) {
    return {
      textStyle: baseTextStyle,
      grid: { left: 40, right: 12, top: 32, bottom: 24 },
      legend: { data: [labelA, labelB], textStyle: { color: THEME.muted, fontFamily: THEME.fontSans } },
      tooltip: { ...tooltipCommon, trigger: "axis" },
      xAxis: { type: "category", data: dates, boundaryGap: false, ...axisCommon },
      yAxis: { type: "value", scale: true, ...axisCommon, axisLine: { show: false } },
      series: [
        { name: labelA, type: "line", data: seriesA, showSymbol: false, lineStyle: { color: THEME.accent, width: 2 } },
        { name: labelB, type: "line", data: seriesB, showSymbol: false, lineStyle: { color: THEME.accentStrong, width: 2, type: "dashed" } },
      ],
    };
  }
  ```
  (`baseTextStyle`/`axisCommon`/`tooltipCommon` are already module-private in `charts.js` —
  this function belongs in that file, not a new one.) A chart with more than one series
  **must** keep the `legend` block — color alone never carries series identity.
- `web/assets/components.js` `viewMeta({ sources, methodology, disclaimer, decisions })` — renders
  the as-of/source/methodology/disclaimer footer required by the root CLAUDE.md, plus an optional
  expandable list of judgment calls (`decisions: [{ question, choice, rationale }]`). Call it with
  real values instead of hand-rolling a footer.
- `web/assets/app.js` — extend `renderMacro`'s existing `segmented` toggle with the new option;
  no new `ROUTES` entry or nav link needed (see above).
- `app/fred.py` already logs provenance (`fred_pull`) on every pull — reuse `FredClient.get_series`
  as-is, no changes needed there for an additive dashboard view.
- TDD control tests (the "write tests first" ones, per the root CLAUDE.md) go in
  `tests/test_analysis.py` under `@pytest.mark.control`; endpoint-level tests go in
  `tests/test_api.py`. Run `make test-control` for the fast, scoped subset — save a full
  `make test` for after everything's wired up.

This map plus `DESIGN.md` is enough to plan an additive dashboard view without spawning
Explore/general-purpose subagents to rediscover backend or frontend patterns — open the specific
file named above directly if you need to confirm exact current syntax.
