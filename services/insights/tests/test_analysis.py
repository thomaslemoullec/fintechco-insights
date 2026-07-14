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
def test_phillips_view_is_deterministic():
    """Same inputs must yield identical output — a reproducibility requirement (SR 11-7)."""
    assert analysis.phillips_view() == analysis.phillips_view()


@pytest.mark.control
def test_phillips_view_carries_asof_source_and_disclaimer():
    """A client-facing figure without as-of date, source, and disclaimer is not shippable."""
    view = analysis.phillips_view()
    assert view["as_of"]
    assert view["sources"]
    assert view["disclaimer"] == analysis.DISCLAIMER


@pytest.mark.control
def test_phillips_decade_stats_are_bounded():
    """Correlation must be a valid Pearson coefficient, and each decade needs enough data
    (>=24 monthly observations) for the estimate to be meaningful rather than noise."""
    decades = analysis.phillips_view()["decades"]
    assert decades
    for d in decades:
        assert -1.0 <= d["corr"] <= 1.0
        assert d["n"] >= 24


@pytest.mark.control
def test_phillips_as_of_matches_latest_point():
    """No look-ahead: the as-of date must be the latest point actually shown, not later."""
    view = analysis.phillips_view()
    assert view["as_of"] == max(p["date"] for p in view["points"])
