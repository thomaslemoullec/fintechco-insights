"""HTTP API for the Macro Insights dashboard."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import analysis
from .indicators import list_indicators

router = APIRouter(prefix="/api")


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
    return analysis.phillips_view()
