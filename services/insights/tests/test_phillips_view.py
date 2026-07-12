"""Control tests for the client-facing Inflation vs. Unemployment (Phillips) view.

These guard the properties that make the figure shippable under CLAUDE.md / SCRUM-7:
- AC1  cleaning/derivation is deterministic and reproducible (SR 11-7);
- AC2  the view carries the data as-of date, source attribution, a methodology note,
       and a disclaimer (model risk / SR 11-7).

Written before the view exists — they define the contract the implementation must meet,
so they are expected to fail until `analysis.phillips_view()` and the
`GET /api/views/phillips` endpoint are built.
"""
from pathlib import Path

import pytest

from app import analysis

_APP_JS = Path(__file__).resolve().parents[1] / "web" / "assets" / "app.js"


# --- Analysis layer: the client-facing payload ------------------------------------------

def _view() -> dict:
    return analysis.phillips_view()


@pytest.mark.control
def test_view_carries_data_as_of_date():
    """AC2 — the view must state the data as-of (vintage) date, and it must be the latest
    month where both series exist (no look-ahead)."""
    view = _view()
    assert view["as_of"] == analysis.as_of()
    # ISO date, and the newest plotted point never post-dates the stated as-of.
    latest = max(p["date"] for p in view["points"])
    assert view["as_of"] == latest


@pytest.mark.control
def test_view_carries_source_attribution():
    """AC2 — authoritative source must be attached (BLS via FRED)."""
    view = _view()
    sources = view["sources"]
    assert isinstance(sources, list) and sources
    blob = " ".join(sources).lower()
    assert "fred" in blob
    assert "bureau of labor statistics" in blob


@pytest.mark.control
def test_view_carries_methodology_note():
    """AC2 — a methodology note describing the year-over-year CPI derivation."""
    method = _view()["methodology"]
    assert isinstance(method, str) and method.strip()
    lowered = method.lower()
    assert "cpi" in lowered
    assert "year-over-year" in lowered or "yoy" in lowered


@pytest.mark.control
def test_view_carries_disclaimer():
    """AC2 — a client-facing disclaimer must be present."""
    disclaimer = _view()["disclaimer"]
    assert isinstance(disclaimer, str) and disclaimer.strip()
    assert disclaimer == analysis.DISCLAIMER


@pytest.mark.control
def test_view_records_methodology_decisions():
    """AC2 — the analyst judgement calls are surfaced with the figure."""
    decisions = _view()["decisions"]
    assert isinstance(decisions, list) and decisions
    for d in decisions:
        assert d["question"] and d["choice"]


@pytest.mark.control
def test_view_cleaning_is_reproducible():
    """AC1 — same inputs must yield an identical payload (deterministic cleaning)."""
    assert analysis.phillips_view() == analysis.phillips_view()


@pytest.mark.control
def test_view_points_are_paired_and_windowed():
    """AC1 — every point pairs unemployment with YoY inflation, tagged by decade, from 1960
    on; inflation stays in a plausible band (a YoY %, not the raw CPI index)."""
    points = _view()["points"]
    assert points
    for p in points:
        assert {"date", "unemployment", "inflation", "decade"} <= p.keys()
        assert p["date"] >= "1960-01-01"
        assert -15.0 <= p["inflation"] <= 25.0


# --- API layer: the disclosures must reach the client over HTTP -------------------------

@pytest.mark.control
def test_api_phillips_returns_disclosures(client):
    """AC2 — the endpoint must serve the as-of date, sources, methodology and disclaimer."""
    resp = client.get("/api/views/phillips")
    assert resp.status_code == 200
    body = resp.json()
    for field in ("as_of", "sources", "methodology", "disclaimer", "points"):
        assert body.get(field)


# --- Routed view: the client-facing rules must hold at the presentation layer -----------

@pytest.mark.control
def test_routed_view_renders_its_own_as_of():
    """AC2 / SR 11-7 — the routed view must show the figure's OWN as-of date: set the pill
    from data.as_of and pass it into the disclosure footer (not rely on a different series)."""
    src = _APP_JS.read_text()
    assert "asof-date" in src and "data.as_of" in src, "view must set the as-of pill from its own payload"
    assert "asOf: data.as_of" in src, "view must pass its as-of date into the viewMeta footer"


@pytest.mark.control
def test_routed_view_variant_selection_is_deterministic():
    """AC1 / SR 11-7 — no hidden randomisation of a client-facing regulated figure; the
    variant must be a deterministic, user-selectable preference (guards against CWE-330)."""
    src = _APP_JS.read_text()
    assert "Math.random" not in src, "client-facing figure must not be assigned via Math.random"
