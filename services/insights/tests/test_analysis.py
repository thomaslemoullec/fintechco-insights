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
def test_inflation_unemployment_view_is_deterministic():
    """SCRUM-7 — same inputs must yield identical output, every call (SR 11-7)."""
    assert analysis.inflation_unemployment_view() == analysis.inflation_unemployment_view()


@pytest.mark.control
def test_inflation_unemployment_view_has_no_unpaired_months():
    """SCRUM-7 — every point must carry both series; build_frame() already drops unpaired months."""
    points = analysis.inflation_unemployment_view()["points"]
    assert points
    assert all(p["inflation"] is not None and p["unemployment"] is not None for p in points)
