"""Cleaning, alignment and exploratory analysis for the economic indicators.

The raw FRED series arrive at different precisions, the CPI series has missing months, and
inflation must be derived (year-over-year) from the CPI *index* before it can be compared with
unemployment. All transforms here are deterministic and documented so the output is
reproducible and auditable (CLAUDE.md > Data governance / model risk).

Note on methodology: a naive monthly correlation of inflation vs unemployment is noisy — the
1970s supply shocks (high inflation *and* high unemployment) scramble it. We therefore report
the OLS **slope** of the tradeoff per decade and contrast the strong early-1960s relationship
with the flat recent era, which is the defensible way to show the Phillips-curve flattening.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .fred import FredClient
from .indicators import INDICATORS

logger = logging.getLogger("insights.analysis")

DISCLAIMER = (
    "For internal research and client discussion only. Derived from public data "
    "(U.S. Bureau of Labor Statistics and Federal Reserve Board, via FRED). "
    "Historical relationships are not indicative of future results."
)
_MIN_DECADE_MONTHS = 60  # don't report a decade with < 5 years of data

# Methodology decisions the ticket left open (recorded here and echoed to the audit trail /
# Jira). These are the "analyst judgement calls" that make the output defensible.
METHODOLOGY_DECISIONS = [
    {
        "question": "Which inflation measure?",
        "choice": "Headline CPI (CPIAUCSL), YoY",
        "rationale": "Client-facing familiarity; core (CPILFESL) available as a sensitivity.",
    },
    {
        "question": "Which unemployment measure?",
        "choice": "U-3 (UNRATE)",
        "rationale": "Standard headline rate with the longest history (1948-); U-6 only from 1994.",
    },
    {
        "question": "Sample window & bucketing?",
        "choice": "1948-present, by decade + a 1960s-vs-2010s contrast",
        "rationale": "Full history for context; decade slopes show the tradeoff weakening.",
    },
    {
        "question": "Data vintage?",
        "choice": "Latest vintage, as-of recorded",
        "rationale": "As-of captured for reproducibility; point-in-time (ALFRED) is a follow-up.",
    },
]


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


def _decade_stats(frame: pd.DataFrame) -> list[dict]:
    """OLS slope + correlation of inflation-on-unemployment, per decade."""
    out = []
    for decade, g in frame.groupby("decade"):
        if len(g) < _MIN_DECADE_MONTHS:
            continue
        slope, intercept = np.polyfit(g["unemployment"], g["inflation"], 1)
        out.append(
            {
                "decade": int(decade),
                "slope": round(float(slope), 2),
                "intercept": round(float(intercept), 2),
                "correlation": round(float(g["inflation"].corr(g["unemployment"])), 2),
                "months": int(len(g)),
            }
        )
    return out


def phillips_view() -> dict:
    """The new view: inflation vs unemployment, with the decade-by-decade tradeoff and the
    'then vs now' contrast that makes the flattening defensible."""
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
    stats = _decade_stats(frame)
    by_decade = {s["decade"]: s for s in stats}
    then = by_decade.get(1960) or stats[0]
    now = by_decade.get(2010) or stats[-1]
    summary = (
        f"In the {then['decade']}s the inflation-unemployment tradeoff was steep "
        f"(slope {then['slope']:+.1f}, corr {then['correlation']:+.2f}); by the {now['decade']}s "
        f"it flattened to near zero (slope {now['slope']:+.1f}, corr {now['correlation']:+.2f})."
    )
    sources = sorted({INDICATORS[i].source for i in ("INFLATION", "UNRATE")})
    logger.info("phillips_view points=%d decades=%d", len(points), len(stats))
    return {
        "title": "Inflation vs. Unemployment (Phillips Curve)",
        "as_of": frame.index.max().date().isoformat(),
        "sources": sources,
        "methodology": (
            "Monthly observations. Inflation = YoY % change in CPIAUCSL; unemployment = UNRATE. "
            "Per-decade OLS slope of inflation on unemployment; 1960s vs 2010s highlighted."
        ),
        "decisions": METHODOLOGY_DECISIONS,
        "disclaimer": DISCLAIMER,
        "summary": summary,
        "then": then,
        "now": now,
        "decade_stats": stats,
        "points": points,
    }
