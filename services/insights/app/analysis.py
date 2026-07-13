"""Cleaning, alignment and exploratory analysis for the economic indicators.

The raw FRED series arrive at different precisions, the CPI series has missing months, and
inflation must be derived (year-over-year) from the CPI *index* before it can be compared with
unemployment. All transforms here are deterministic and documented so the output is
reproducible and auditable (CLAUDE.md > Data governance / model risk).
"""
from __future__ import annotations

import pandas as pd

from .fred import FredClient
from .indicators import INDICATORS

DISCLAIMER = (
    "For internal research and client discussion only. Derived from public data "
    "(U.S. Bureau of Labor Statistics and Federal Reserve Board, via FRED). "
    "Historical relationships are not indicative of future results."
)


def _client() -> FredClient:
    return FredClient()


def _monthly(df: pd.DataFrame, col: str) -> pd.Series:
    return df.set_index("DATE").asfreq("MS")[col]


def _fill_gaps(series: pd.Series) -> pd.Series:
    """Fill a missing month using only the last published reading — never a later one.

    `Series.interpolate(method="time")` fills an interior gap using the values on BOTH
    sides, which for a historical gap means using data from a month that would not yet
    have been published at that point in time (no-look-ahead / no-leakage, CLAUDE.md >
    Data governance). A forward-fill carries the last known value forward instead.
    """
    return series.ffill()


def build_frame() -> pd.DataFrame:
    """Clean + align inflation and unemployment (and fed funds) onto one monthly index."""
    client = _client()
    cpi = _fill_gaps(_monthly(client.get_series("CPIAUCSL"), "CPIAUCSL"))
    unrate = _monthly(client.get_series("UNRATE"), "UNRATE")
    fedfunds = _monthly(client.get_series("FEDFUNDS"), "FEDFUNDS")

    frame = pd.DataFrame(index=cpi.index)
    frame["inflation"] = cpi.pct_change(12) * 100.0  # YoY %, needs 12 months of history
    frame["unemployment"] = unrate
    frame["fed_funds"] = fedfunds
    frame = frame.dropna(subset=["inflation", "unemployment"])
    frame["decade"] = (frame.index.year // 10) * 10
    return frame


def as_of() -> str:
    return build_frame().index.max().date().isoformat()


def phillips_view() -> dict:
    """Paired inflation/unemployment points (by decade) for the Phillips-curve relationship view."""
    frame = build_frame()
    # The decade color ramp (web/DESIGN.md) is only defined for the 1960s-2030s; scope the
    # view to that range rather than rendering earlier decades in an indistinguishable color.
    frame = frame[frame["decade"] >= 1960]
    points = [
        {
            "date": d.date().isoformat(),
            "inflation": round(float(row.inflation), 2),
            "unemployment": round(float(row.unemployment), 2),
            "decade": int(row.decade),
        }
        for d, row in frame.iterrows()
    ]
    return {
        "as_of": frame.index.max().date().isoformat(),
        "sources": [
            INDICATORS["INFLATION"].source + " (CPIAUCSL)",
            INDICATORS["UNRATE"].source + " (UNRATE)",
        ],
        "methodology": (
            "Inflation is the year-over-year % change of the CPI index (CPIAUCSL); "
            "unemployment is the seasonally adjusted civilian rate (UNRATE). Both are "
            "aligned to a common monthly index; missing CPI months are forward-filled "
            "from the last published reading before computing the year-over-year change. "
            "Points are grouped by decade."
        ),
        "disclaimer": DISCLAIMER,
        "decisions": [
            {
                "question": "How are missing CPI months handled?",
                "choice": "Forward-filled from the last published reading",
                "rationale": "Never uses a later, not-yet-available reading to fill a historical "
                "gap — avoids look-ahead bias (CLAUDE.md > no look-ahead / no leakage).",
            },
            {
                "question": "Why year-over-year rather than month-over-month?",
                "choice": "Year-over-year % change",
                "rationale": "Standard inflation convention; smooths seasonal noise in the monthly index.",
            },
            {
                "question": "Why does the history start in 1960?",
                "choice": "Points before 1960 are excluded",
                "rationale": "The chart's decade color legend is only defined for the 1960s-2030s; "
                "earlier points would be indistinguishable rather than dropped silently.",
            },
        ],
        "points": points,
    }


def series_view(indicator_id: str) -> dict:
    ind = INDICATORS.get(indicator_id)
    if ind is None:
        raise KeyError(indicator_id)
    frame = build_frame()
    col = {
        "UNRATE": "unemployment",
        "INFLATION": "inflation",
        "FEDFUNDS": "fed_funds",
    }[indicator_id]
    s = frame[col].dropna()
    points = [{"date": d.date().isoformat(), "value": round(float(v), 2)} for d, v in s.items()]
    methodology = (
        f"{ind.title}: year-over-year % change of the {ind.series_id} index."
        if ind.transform == "yoy"
        else f"{ind.title}: {ind.description}"
    )
    return {
        "indicator": ind.to_dict(),
        "as_of": frame.index.max().date().isoformat(),
        "methodology": methodology,
        "disclaimer": DISCLAIMER,
        "points": points,
    }
