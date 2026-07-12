"""Cleaning, alignment and exploratory analysis for the economic indicators.

The raw FRED series arrive at different precisions, the CPI series has missing months, and
inflation must be derived (year-over-year) from the CPI *index* before it can be compared with
unemployment. All transforms here are deterministic and documented so the output is
reproducible and auditable (CLAUDE.md > Data governance / model risk).
"""
from __future__ import annotations

import numpy as np
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


# Start of the aligned window. Applied AFTER the YoY transform so the first retained
# month (Jan 1960) is derived from 1959 CPI — no look-ahead. See METHODOLOGY_DECISIONS.
START = "1960-01-01"

# Analyst judgement calls the ticket leaves open, recorded so they can be surfaced in the
# client-facing disclosure footer (viewMeta) and attached to the ticket
# (CLAUDE.md > Model risk / reproducibility).
METHODOLOGY_DECISIONS = [
    {
        "question": "How are missing CPI months handled before deriving YoY inflation?",
        "choice": "Forward-fill (last observation carried forward)",
        "rationale": "Uses only prior observations, so no in-gap look-ahead; reflects as-reported data.",
    },
    {
        "question": "What history window does the view cover?",
        "choice": "From January 1960",
        "rationale": "Aligns with the decade colour ramp (1960s–2030s) so every plotted decade has a defined colour.",
    },
    {
        "question": "Which data vintage is used?",
        "choice": "Latest revised (FRED default)",
        "rationale": "Standard for a descriptive research view; figures reflect current revisions, stated in the note.",
    },
    {
        "question": "How is inflation derived?",
        "choice": "Year-over-year % change of the CPI index (12-month)",
        "rationale": "Per AC1; a trailing 12-month change, computed before the 1960 window so Jan 1960 uses 1959 CPI.",
    },
]


def _monthly(df: pd.DataFrame, col: str) -> pd.Series:
    return df.set_index("DATE").asfreq("MS")[col]


def build_frame() -> pd.DataFrame:
    """Clean + align inflation and unemployment (and fed funds) onto one monthly index.

    Missing CPI months are forward-filled (LOCF) — only prior observations are used, so no
    in-gap look-ahead. Inflation is the YoY % change of the CPI index, computed on full
    history *before* the 1960 window is applied so Jan 1960 is derived from 1959 CPI. All
    transforms are deterministic and documented (see METHODOLOGY_DECISIONS).
    """
    client = _client()
    cpi = _monthly(client.get_series("CPIAUCSL"), "CPIAUCSL").ffill()
    unrate = _monthly(client.get_series("UNRATE"), "UNRATE")
    fedfunds = _monthly(client.get_series("FEDFUNDS"), "FEDFUNDS")

    frame = pd.DataFrame(index=cpi.index)
    frame["inflation"] = cpi.pct_change(12) * 100.0  # YoY %, needs 12 months of history
    frame["unemployment"] = unrate
    frame["fed_funds"] = fedfunds
    frame = frame.dropna(subset=["inflation", "unemployment"])
    frame = frame[frame.index >= START]  # window applied AFTER YoY so 1960 uses 1959 CPI
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


def _ols(x: pd.Series, y: pd.Series) -> dict:
    """Deterministic OLS fit y ~ x. In-sample and descriptive only — not a forecast."""
    slope, intercept = np.polyfit(x.to_numpy(dtype=float), y.to_numpy(dtype=float), 1)
    x0, x1 = float(x.min()), float(x.max())
    return {
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "x0": round(x0, 2), "y0": round(float(slope * x0 + intercept), 2),
        "x1": round(x1, 2), "y1": round(float(slope * x1 + intercept), 2),
        "note": "In-sample OLS fit of inflation on unemployment — descriptive, not predictive.",
    }


def phillips_view() -> dict:
    """Client-facing Inflation vs. Unemployment (Phillips) payload.

    Paired monthly points (unemployment, YoY inflation, decade) plus a fitted trend, with the
    data as-of date, source attribution, methodology note, disclaimer and the recorded
    methodology decisions — every disclosure travels with the figure (SCRUM-7 AC1/AC2).
    """
    frame = build_frame()
    cpi = INDICATORS["INFLATION"]
    unrate = INDICATORS["UNRATE"]
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
        "sources": [
            f"{cpi.title} ({cpi.series_id}) — {cpi.source}",
            f"{unrate.title} ({unrate.series_id}) — {unrate.source}",
        ],
        "methodology": (
            "Inflation is the year-over-year % change of the CPI index (CPIAUCSL), plotted "
            "against the U-3 unemployment rate (UNRATE). Missing CPI months are forward-filled; "
            "monthly frequency, from January 1960; latest revised vintage."
        ),
        "disclaimer": DISCLAIMER,
        "decisions": METHODOLOGY_DECISIONS,
        "fit": _ols(frame["unemployment"], frame["inflation"]),
        "points": points,
    }
