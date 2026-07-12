"""FinTechCo Macro Insights — FastAPI entrypoint.

One process serves both the JSON API (`/api/*`) and the static dashboard UI (`/`).
Run: `make dev`  ->  uvicorn app.main:app --reload --app-dir services/insights
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="FinTechCo Macro Insights", version="0.1.0")
app.include_router(api_router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


# Serve the static SPA last so /api and /healthz take precedence over the catch-all mount.
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/", StaticFiles(directory=_WEB_DIR, html=True), name="web")
