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
    first = analysis.build_frame()
    second = analysis.build_frame()
    assert first.equals(second)


@pytest.mark.control
def test_phillips_points_have_no_missing_values():
    """No NaN/inf may reach a client-facing view."""
    view = analysis.phillips_view()
    assert view["points"], "expected at least some points"
    for p in view["points"]:
        assert math.isfinite(p["inflation"])
        assert math.isfinite(p["unemployment"])


@pytest.mark.control
def test_phillips_view_carries_required_disclosures():
    """Client-facing output must state as-of date, source(s), methodology and a disclaimer."""
    view = analysis.phillips_view()
    assert view["as_of"]  # non-empty ISO date
    assert view["sources"], "must attribute a source"
    assert view["methodology"].strip()
    assert "not indicative of future results" in view["disclaimer"].lower()


def test_inflation_is_year_over_year():
    """Derived inflation must be YoY % change of the CPI index, not the raw index."""
    view = analysis.series_view("INFLATION")
    # YoY inflation lives in a plausible band across 1961-2024; the raw index (~30-300) would not.
    values = [p["value"] for p in view["points"]]
    assert all(-5.0 <= v <= 20.0 for v in values)


def test_flattening_is_present():
    """The tradeoff must weaken over time: |corr| in the newest decade < oldest decade."""
    corr = analysis.phillips_view()["decade_correlations"]
    assert abs(corr[-1]["correlation"]) < abs(corr[0]["correlation"])
