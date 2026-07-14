"""Data-governance / model-risk tests for the analysis layer.

The @pytest.mark.control tests guard the properties that make a client-facing figure
shippable under CLAUDE.md: reproducibility, provenance/disclosure, and clean data.
"""
import pytest
from app import analysis


@pytest.mark.control
def test_cleaning_is_deterministic():
    """Same inputs must yield identical output — a reproducibility requirement (SR 11-7)."""
    assert analysis.build_frame().equals(analysis.build_frame())


def test_inflation_is_year_over_year():
    """Derived inflation must be YoY % change (a plausible band), not the raw CPI index."""
    values = [p["value"] for p in analysis.series_view("INFLATION")["points"]]
    assert all(-15.0 <= v <= 25.0 for v in values)


@pytest.mark.control
def test_series_view_carries_disclaimer():
    """Every client-facing series view must carry the model-risk disclaimer (AC2 / SR 11-7)."""
    view = analysis.series_view("INFLATION")
    assert view["disclaimer"] == analysis.DISCLAIMER
    assert view["disclaimer"]


@pytest.mark.control
def test_inflation_and_unemployment_share_dates():
    """Inflation vs. unemployment views join the two series by date client-side; the join is
    only safe if both series cover the exact same set of dates (guards against a silently
    misaligned client-facing figure)."""
    inflation_dates = {p["date"] for p in analysis.series_view("INFLATION")["points"]}
    unemployment_dates = {p["date"] for p in analysis.series_view("UNRATE")["points"]}
    assert inflation_dates == unemployment_dates
