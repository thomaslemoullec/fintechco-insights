"""Data source layer for FRED economic series.

The FRED API key is read from the environment (`FRED_API_KEY`), which in production is injected
from Secret Manager (secret `fred-api-key`) — never hardcoded (CLAUDE.md > Secrets).

Series are cached to disk (`app/data/<series_id>.csv`) so the app is reproducible and works
offline / on Cloud Run without a live call on every request. `FRED_LIVE=1` forces a refresh
from the API. Every access emits a provenance log line (series id, rows, as-of, source) — the
local stand-in for the audit stream that goes to the SIEM in production.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger("insights.fred")

# httpx logs each request's full URL at INFO by default — our request carries api_key as a
# query param (FRED's API only accepts it that way), so that logger must never reach INFO.
logging.getLogger("httpx").setLevel(logging.WARNING)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredClient:
    def __init__(self, api_key: str | None = None, data_dir: Path | None = None) -> None:
        # Key comes from the environment (injected from Secret Manager in prod).
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        self.data_dir = data_dir or _DATA_DIR
        self.live = bool(os.environ.get("FRED_LIVE"))

    def get_series(self, series_id: str) -> pd.DataFrame:
        """Return a two-column frame [DATE, <series_id>], from cache or the live API."""
        cache = self.data_dir / f"{series_id}.csv"
        if self.live or not cache.exists():
            df = self._fetch(series_id)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache, index=False)
            origin = "live FRED API"
        else:
            df = pd.read_csv(cache, parse_dates=["DATE"])
            origin = "cached fixture"

        as_of = df["DATE"].max().date().isoformat()
        logger.info(
            "provenance: series=%s rows=%d as_of=%s source=%s",
            series_id, len(df), as_of, origin,
        )
        return df

    def _fetch(self, series_id: str) -> pd.DataFrame:
        """Fetch a series from the FRED API and normalise it (strings, '.' -> NaN, dates)."""
        if not self.api_key:
            raise RuntimeError(
                "FRED_API_KEY missing from the environment "
                "(in production it is injected from Secret Manager secret 'fred-api-key')."
            )
        import httpx

        params = {"series_id": series_id, "api_key": self.api_key, "file_type": "json"}
        try:
            resp = httpx.get(_FRED_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            # Never let the underlying exception propagate: httpx.HTTPStatusError and
            # httpx.RequestError both embed the full request URL (including api_key) in
            # their message/repr, which would otherwise land in an uncaught-error log.
            status = getattr(getattr(exc, "response", None), "status_code", "no response")
            raise RuntimeError(
                f"FRED API request failed for series {series_id!r} (status {status})"
            ) from None
        obs = resp.json().get("observations", [])
        df = pd.DataFrame(obs)[["date", "value"]]
        # FRED encodes missing values as the string "." — coerce to NaN, values to float.
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.rename(columns={"date": "DATE", "value": series_id})
        df["DATE"] = pd.to_datetime(df["DATE"])
        return df
