"""Refresh the FRED series cache from the live API.

Reads FRED_API_KEY from the environment (in production: Secret Manager secret `fred-api-key`).
Writes one CSV per series into services/insights/app/data/ — the cache the app serves from.

Run: `make fetch`  (or `FRED_API_KEY=... python scripts/fetch_fred.py`)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "insights"))

from app.fred import FredClient  # noqa: E402

SERIES = ["CPIAUCSL", "CPILFESL", "UNRATE", "U6RATE", "FEDFUNDS"]


def main() -> None:
    os.environ["FRED_LIVE"] = "1"  # force a live pull + cache write
    client = FredClient()
    for sid in SERIES:
        df = client.get_series(sid)
        rng = f"{df['DATE'].min().date()}..{df['DATE'].max().date()}"
        print(f"{sid}: {len(df)} rows {rng}")


if __name__ == "__main__":
    main()
