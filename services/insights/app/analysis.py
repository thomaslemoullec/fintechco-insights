"""Cleaning, alignment and exploratory analysis for the economic indicators.

This is the "real work": the raw FRED series arrive at different precisions, the CPI series has
missing months, and inflation must be derived (year-over-year) from the CPI *index* before it
can be compared with unemployment. All transforms here are deterministic and documented so the
output is reproducible and auditable (CLAUDE.md > Data governance / model risk).
"""
from __future__ import annotations

import logging

import pandas as pd

from .fred import FredClient
from .indicators import INDICATORS

logger = logging.getLogger("insights.analysis")

DISCLAIMER = (
    "For internal research and client discussion only. Derived from public data "
    "(U.S. Bureau of Labor Statistics and Federal Reserve Board, via FRED). "
    "Historical relationships are not indicative of future results."
)
_MIN_DECADE_MONTHS = 24  # don't report a correlation for a decade with too little data


def _client() -> FredClient:
    return FredClient()


def _monthly(df: pd.DataFrame, col: str) -> pd.Series:
    """Index by DATE at monthly-start frequency, exposing gaps as NaN."""
    return df.set_index("DATE").asfreq("MS")[col]


def build_frame() -> pd.DataFrame:
    """Clean + align inflation, unemployment and the fed funds rate onto one monthly index.

    Cleaning steps (order matters, all deterministic):
      1. Put each series on a continuous month-start index (missing months -> NaN).
      2. Time-interpolate the CPI index to fill the gaps, then derive YoY inflation from it.
      3. Join on date and drop the leading rows where YoY is undefined (first 12 months).
    """
    client = _client()
    cpi = _monthly(client.get_series("CPIAUCSL"), "CPIAUCSL").interpolate(method="time")
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
    frame = build_frame()
    return frame.index.max().date().isoformat()


def series_view(indicator_id: str) -> dict:
    """A single cleaned time series for the existing line-chart views."""
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
    return {
        "indicator": ind.to_dict(),
        "as_of": frame.index.max().date().isoformat(),
        "points": points,
    }


def decade_correlations(frame: pd.DataFrame) -> list[dict]:
    out = []
    for decade, group in frame.groupby("decade"):
        if len(group) < _MIN_DECADE_MONTHS:
            continue
        corr = float(group["inflation"].corr(group["unemployment"]))
        out.append(
            {"decade": int(decade), "correlation": round(corr, 3), "months": int(len(group))}
        )
    return out


def phillips_view() -> dict:
    """The new view: inflation vs unemployment, with the decade-by-decade tradeoff.

    Returns the scatter points plus the correlation per decade, which is what makes the
    'flattening' visible: a strong negative correlation early, decaying toward zero.
    """
    frame = build_frame()
    points = [
        {
            "date": d.date().isoformat(),
            "unemployment": round(float(r.unemployment), 2),
            "inflation": round(float(r.inflation), 2),
            "decade": int(r.decade),
        }
        for d, r in frame.iterrows()
    ]
    corr_by_decade = decade_correlations(frame)
    first, last = corr_by_decade[0], corr_by_decade[-1]
    summary = (
        f"The inflation-unemployment tradeoff weakened from {first['correlation']:+.2f} "
        f"in the {first['decade']}s to {last['correlation']:+.2f} in the {last['decade']}s."
    )
    sources = sorted({INDICATORS[i].source for i in ("INFLATION", "UNRATE")})
    logger.info("phillips_view points=%d decades=%d", len(points), len(corr_by_decade))
    return {
        "title": "Inflation vs. Unemployment (Phillips Curve)",
        "as_of": frame.index.max().date().isoformat(),
        "sources": sources,
        "methodology": (
            "Monthly observations, 1961-2024. Inflation is the year-over-year % change in "
            "CPIAUCSL; unemployment is UNRATE. Correlation computed per calendar decade."
        ),
        "disclaimer": DISCLAIMER,
        "summary": summary,
        "decade_correlations": corr_by_decade,
        "points": points,
    }
