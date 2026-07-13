"""Data-governance / model-risk tests for the analysis layer.

The @pytest.mark.control tests guard the properties that make a client-facing figure
shippable under CLAUDE.md: reproducibility, provenance/disclosure, and clean data.
"""
import pandas as pd
import pytest
from app import analysis


@pytest.mark.control
def test_cleaning_is_deterministic():
    """Same inputs must yield identical output — a reproducibility requirement (SR 11-7)."""
    assert analysis.build_frame().equals(analysis.build_frame())


@pytest.mark.control
def test_gap_filling_has_no_look_ahead():
    """A missing month must be filled from prior data only, never a later reading."""
    idx = pd.date_range("2020-01-01", periods=4, freq="MS")
    series = pd.Series([100.0, None, None, 400.0], index=idx)
    filled = analysis._fill_gaps(series)
    # A two-sided (e.g. time-weighted) interpolation would place the gap values between
    # 100 and 400. A forward-only fill must carry the last known value (100) instead.
    assert filled.iloc[1] == 100.0
    assert filled.iloc[2] == 100.0


def test_inflation_is_year_over_year():
    """Derived inflation must be YoY % change (a plausible band), not the raw CPI index."""
    values = [p["value"] for p in analysis.series_view("INFLATION")["points"]]
    assert all(-15.0 <= v <= 25.0 for v in values)


@pytest.mark.control
def test_phillips_view_is_deterministic():
    """Same inputs must yield identical output — a reproducibility requirement (SR 11-7)."""
    assert analysis.phillips_view() == analysis.phillips_view()


@pytest.mark.control
def test_phillips_view_carries_disclosures():
    """A client-facing figure must carry as-of, source attribution, methodology and disclaimer."""
    view = analysis.phillips_view()
    assert view["as_of"]
    assert view["sources"]
    assert view["methodology"]
    assert view["disclaimer"]
    assert view["points"]


def test_phillips_view_points_are_paired_and_bucketed():
    """Each point must carry both series plus the decade bucket used for the chart legend."""
    for point in analysis.phillips_view()["points"]:
        assert {"date", "inflation", "unemployment", "decade"} <= point.keys()
        assert -15.0 <= point["inflation"] <= 25.0
        assert 0.0 <= point["unemployment"] <= 30.0
        assert point["decade"] % 10 == 0
        # Scoped to the decades the chart's color ramp actually defines (web/DESIGN.md).
        assert 1960 <= point["decade"] <= 2030
