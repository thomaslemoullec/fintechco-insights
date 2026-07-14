# FinTechCo — Macro Insights

Internal **economic-indicators dashboard** for the Macro Research desk. It pulls public
economic series (from FRED), cleans and aligns them, and presents them as client-ready views
for research and client discussions.

- **Backend:** Python / FastAPI (`services/insights/app/`) — data source layer, cleaning &
  exploratory analysis, and a JSON API.
- **Frontend:** a static dashboard (`services/insights/web/`) served by the same FastAPI
  process. Follows the design system in [`services/insights/web/DESIGN.md`](services/insights/web/DESIGN.md).
- **Data:** economic series from FRED, cached as committed CSVs (`services/insights/app/data/`)
  — public, non-personal data only. `scripts/gen_fixtures.py` is an offline synthetic fallback.

## Run

```bash
make setup     # venv + deps + generate fixtures
make dev       # http://127.0.0.1:8000
make test      # full suite
```

Engineering conventions (they are controls, not style) live in [`CLAUDE.md`](CLAUDE.md).
