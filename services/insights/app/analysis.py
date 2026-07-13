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
    # Missing CPI months are left as NaN and dropped downstream — never interpolated.
    # Interpolating would pull a *later* month's figure back to fill an earlier gap
    # (look-ahead leakage) and would contradict the client-facing methodology note.
    cpi = _monthly(client.get_series("CPIAUCSL"), "CPIAUCSL")
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
    """Client-facing inflation-vs-unemployment (Phillips) relationship, with disclosures.

    Reuses ``build_frame`` (deterministic YoY inflation + monthly alignment). Each point
    is a monthly (unemployment, inflation) pair tagged with its decade for the category
    legend. Carries the full disclosure set (as-of / source / methodology / disclaimer)
    required for a client-facing figure (CLAUDE.md > Model risk; SR 11-7).
    """
    frame = build_frame()[["unemployment", "inflation", "decade"]].dropna()
    points = [
        {
            "date": d.date().isoformat(),
            "unemployment": round(float(row.unemployment), 2),
            "inflation": round(float(row.inflation), 2),
            "decade": int(row.decade),
        }
        for d, row in frame.iterrows()
    ]
    return {
        "as_of": frame.index.max().date().isoformat(),
        "points": points,
        "sources": [
            "U.S. Bureau of Labor Statistics — CPI (CPIAUCSL), via FRED",
            "U.S. Bureau of Labor Statistics — Unemployment rate (UNRATE), via FRED",
        ],
        "methodology": (
            "Inflation is the year-over-year % change of the headline CPI index; "
            "unemployment is the monthly civilian rate. Series are aligned on a monthly "
            "index; months missing a published figure are dropped, not interpolated."
        ),
        "disclaimer": DISCLAIMER,
        "decisions": [
            {
                "question": "Which CPI series?",
                "choice": "Headline CPI (CPIAUCSL)",
                "rationale": "matches the classic Phillips-curve framing used with clients",
            },
            {
                "question": "How to handle missing CPI months?",
                "choice": "Drop, do not interpolate",
                "rationale": "never fabricate a published figure, or use later data to fill "
                "an earlier gap",
            },
        ],
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
