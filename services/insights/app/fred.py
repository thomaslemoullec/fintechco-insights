"""Data source layer for FRED economic series.

Production intent: pull series from the FRED API (https://fred.stlouisfed.org). The API key
is read from the environment (`FRED_API_KEY`) — never hardcoded — consistent with CLAUDE.md >
Secrets. Until live API access is provisioned, we serve the same series from committed
synthetic fixtures (see scripts/gen_fixtures.py); the calling code and shape are identical, so
switching to live mode is a one-line change (`_load_live`).

Every pull emits a provenance log line (series id, row count, as-of, source) so that any
figure shown to a client can be traced back to its source and vintage — a data-governance
requirement, and the local stand-in for the audit stream that would go to the SIEM in prod.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger("insights.fred")

_DATA_DIR = Path(__file__).resolve().parent / "data"


class FredClient:
    def __init__(self, api_key: str | None = None, data_dir: Path | None = None) -> None:
        # Credentials come from the environment, never source. Absence is tolerated only
        # because we are in fixture mode; live mode requires the key.
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        self.data_dir = data_dir or _DATA_DIR
        self.live = bool(os.environ.get("FRED_LIVE"))

    def get_series(self, series_id: str) -> pd.DataFrame:
        """Return a two-column frame [DATE, <series_id>] for the requested series."""
        if self.live:
            df = self._load_live(series_id)
            mode = "api"
        else:
            df = self._load_fixture(series_id)
            mode = "fixture"

        as_of = df["DATE"].max().date().isoformat() if not df.empty else "n/a"
        # Provenance: who/what/when — no PII, just the series identity and vintage.
        logger.info(
            "fred_pull series=%s rows=%d as_of=%s source=%s",
            series_id, len(df), as_of, mode,
        )
        return df

    def _load_fixture(self, series_id: str) -> pd.DataFrame:
        path = self.data_dir / f"{series_id}.csv"
        if not path.exists():
            raise FileNotFoundError(f"no fixture for series {series_id!r} at {path}")
        return pd.read_csv(path, parse_dates=["DATE"])

    def _load_live(self, series_id: str) -> pd.DataFrame:  # pragma: no cover
        if not self.api_key:
            raise RuntimeError("FRED_LIVE set but FRED_API_KEY is missing from the environment")
        raise NotImplementedError(
            "Live FRED pull not yet wired. Set FRED_API_KEY and implement the fredapi call here."
        )
