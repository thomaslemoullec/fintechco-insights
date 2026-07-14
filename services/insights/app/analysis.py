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


def build_frame() -> pd.DataFrame:
    """Clean + align inflation and unemployment (and fed funds) onto one monthly index."""
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
    return build_frame().index.max().date().isoformat()


def phillips_view() -> dict:
    """Inflation vs. unemployment, combined for the Phillips-curve view.

    Correlation/slope are computed per calendar decade (>=24 monthly observations) rather
    than over the full history: a single full-sample statistic would conflate regime shifts
    (e.g. 1970s stagflation) into one misleading number (CLAUDE.md > No unsupported claims).
    """
    frame = build_frame()
    points = [
        {"date": d.date().isoformat(), "inflation": round(float(i), 2), "unemployment": round(float(u), 2)}
        for d, i, u in zip(frame.index, frame["inflation"], frame["unemployment"])
    ]

    decades = []
    for decade, group in frame.groupby("decade"):
        if len(group) < 24:
            continue
        corr = group["inflation"].corr(group["unemployment"])
        slope = group["unemployment"].cov(group["inflation"]) / group["unemployment"].var()
        decades.append(
            {"decade": int(decade), "n": int(len(group)), "corr": round(float(corr), 2), "slope": round(float(slope), 2)}
        )

    sources = sorted({INDICATORS["INFLATION"].source, INDICATORS["UNRATE"].source})
    return {
        "as_of": frame.index.max().date().isoformat(),
        "sources": sources,
        "disclaimer": DISCLAIMER,
        "points": points,
        "decades": decades,
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
    return {
        "indicator": ind.to_dict(),
        "as_of": frame.index.max().date().isoformat(),
        "points": points,
    }
