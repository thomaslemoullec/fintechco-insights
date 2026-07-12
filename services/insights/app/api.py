"""HTTP API for the Macro Insights dashboard."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import analysis
from .indicators import list_indicators
from .news import list_news

router = APIRouter(prefix="/api")
ab_logger = logging.getLogger("insights.ab")

# The two chart treatments selected to run as an A/B experiment for the Phillips view.
AB_VARIANTS = ["by-decade", "then-vs-now"]


@router.get("/news")
def get_news() -> dict:
    return {"news": list_news()}


@router.get("/indicators")
def get_indicators() -> dict:
    return {"indicators": list_indicators()}


@router.get("/series/{indicator_id}")
def get_series(indicator_id: str) -> dict:
    try:
        return analysis.series_view(indicator_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown indicator {indicator_id!r}") from exc


@router.get("/views/phillips")
def get_phillips_view() -> dict:
    view = analysis.phillips_view()
    view["ab_variants"] = AB_VARIANTS
    return view


class ABEvent(BaseModel):
    variant: str
    view: str = "phillips"


@router.post("/ab/event")
def record_ab_event(event: ABEvent) -> dict:
    """Log an A/B variant impression to the audit trail (no PII — just which variant was shown)."""
    if event.variant not in AB_VARIANTS:
        raise HTTPException(status_code=400, detail=f"unknown variant {event.variant!r}")
    ab_logger.info("ab_impression view=%s variant=%s", event.view, event.variant)
    return {"ok": True}
