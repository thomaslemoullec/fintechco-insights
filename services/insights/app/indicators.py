"""Catalogue of economic indicators surfaced by the dashboard.

Each entry is metadata only — the actual observations come from the data source layer
(`fred.py`). Keeping provenance (source, series id, units, frequency) beside every series is
a data-governance requirement: any client-facing number must be traceable to an authoritative
source. See CLAUDE.md > Data governance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Indicator:
    id: str
    title: str
    units: str
    frequency: str
    source: str
    series_id: str  # upstream FRED series id
    transform: str = "level"  # "level" | "yoy"
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# The series the dashboard knows about. INFLATION is derived (year-over-year % change of the
# CPI index) rather than pulled directly — the transform is recorded so it stays auditable.
INDICATORS: dict[str, Indicator] = {
    "UNRATE": Indicator(
        id="UNRATE",
        title="Unemployment Rate",
        units="Percent",
        frequency="Monthly",
        source="U.S. Bureau of Labor Statistics via FRED",
        series_id="UNRATE",
        description="Civilian unemployment rate, seasonally adjusted.",
    ),
    "INFLATION": Indicator(
        id="INFLATION",
        title="Inflation (CPI, YoY)",
        units="Percent",
        frequency="Monthly",
        source="U.S. Bureau of Labor Statistics via FRED",
        series_id="CPIAUCSL",
        transform="yoy",
        description="Year-over-year % change in the Consumer Price Index (All Urban Consumers).",
    ),
    "FEDFUNDS": Indicator(
        id="FEDFUNDS",
        title="Federal Funds Rate",
        units="Percent",
        frequency="Monthly",
        source="Federal Reserve Board via FRED",
        series_id="FEDFUNDS",
        description="Effective federal funds rate, monthly average.",
    ),
}


def list_indicators() -> list[dict]:
    return [ind.to_dict() for ind in INDICATORS.values()]
