"""Data-governance / model-risk tests for the analysis layer.

The @pytest.mark.control tests guard the properties that make a client-facing figure
shippable under CLAUDE.md: reproducibility, provenance/disclosure, and clean data.
"""
import math

import pytest
from app import analysis


@pytest.mark.control
def test_cleaning_is_deterministic():
    """Same inputs must yield identical output — a reproducibility requirement (SR 11-7)."""
    assert analysis.build_frame().equals(analysis.build_frame())


@pytest.mark.control
def test_phillips_points_have_no_missing_values():
    """No NaN/inf may reach a client-facing view."""
    view = analysis.phillips_view()
    assert view["points"]
    for p in view["points"]:
        assert math.isfinite(p["inflation"])
        assert math.isfinite(p["unemployment"])


@pytest.mark.control
def test_phillips_view_carries_required_disclosures():
    """Client-facing output must state as-of date, source(s), methodology and a disclaimer."""
    view = analysis.phillips_view()
    assert view["as_of"]
    assert view["sources"]
    assert view["methodology"].strip()
    assert "not indicative of future results" in view["disclaimer"].lower()


@pytest.mark.control
def test_methodology_decisions_are_recorded():
    """The analyst judgement calls must be captured for the audit trail."""
    decisions = analysis.phillips_view()["decisions"]
    assert decisions
    for d in decisions:
        assert d["question"] and d["choice"] and d["rationale"]


def test_inflation_is_year_over_year():
    """Derived inflation must be YoY % change (a plausible band), not the raw CPI index."""
    values = [p["value"] for p in analysis.series_view("INFLATION")["points"]]
    assert all(-15.0 <= v <= 25.0 for v in values)


def test_flattening_is_present():
    """The tradeoff must weaken: the recent-era slope magnitude < the early-era slope magnitude."""
    view = analysis.phillips_view()
    assert abs(view["now"]["slope"]) < abs(view["then"]["slope"])
