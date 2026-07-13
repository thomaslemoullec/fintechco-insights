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
def test_phillips_view_carries_full_disclosure_set():
    """A client-facing figure is shippable only with as-of / source / methodology /
    disclaimer (CLAUDE.md > Model risk; SR 11-7, AC2)."""
    view = analysis.phillips_view()
    assert view["as_of"]
    assert view["sources"] and all(view["sources"])
    assert view["methodology"] and view["disclaimer"]
    assert view["points"] and all(
        {"date", "unemployment", "inflation", "decade"} <= p.keys() for p in view["points"]
    )


@pytest.mark.control
def test_phillips_view_is_reproducible():
    """Same inputs must yield an identical payload — reproducibility (SR 11-7, AC1)."""
    assert analysis.phillips_view() == analysis.phillips_view()
