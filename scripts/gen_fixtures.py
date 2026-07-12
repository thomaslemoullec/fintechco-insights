"""Generate synthetic FRED-style fixtures for the Macro Insights dashboard.

The real service will pull these series from the FRED API (see services/insights/app/fred.py).
Until API access is wired up, we ship deterministic synthetic fixtures that mimic the FRED
CSV shape (a DATE column plus the series column named after its FRED series id) so the
cleaning / analysis code exercises the same code paths it will in production.

The synthetic model deliberately encodes the *flattening of the Phillips curve*: a strong
inflation<->unemployment tradeoff in the 1960s-1980s that decays to near-zero by the 2000s-2020s.

Run: `make seed`  (or `python scripts/gen_fixtures.py`)
Deterministic: fixed seed -> identical output every run (a reproducibility requirement).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / "services" / "insights" / "app" / "data"
START_YEAR = 1960
END_YEAR = 2024
SEED = 42


def _months() -> list[str]:
    out = []
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            out.append(f"{year}-{month:02d}-01")
    return out


def _decade(year: int) -> int:
    return (year // 10) * 10


# Phillips-curve slope by decade: how strongly low unemployment pushes inflation up.
# High in the 60s-80s (a real tradeoff), collapsing toward ~0 by the 2000s-2020s.
_SLOPE = {1960: 1.15, 1970: 1.30, 1980: 0.95, 1990: 0.55, 2000: 0.22, 2010: 0.08, 2020: 0.06}
# Baseline inflation level by decade (the Great Inflation of the 70s-80s, low-flation 2010s).
_BASE_INFL = {1960: 2.4, 1970: 6.8, 1980: 5.2, 1990: 3.0, 2000: 2.5, 2010: 1.7, 2020: 3.6}
# Natural rate of unemployment by decade (u*), the pivot of the tradeoff.
_USTAR = {1960: 5.0, 1970: 6.2, 1980: 6.5, 1990: 5.6, 2000: 5.0, 2010: 4.8, 2020: 4.3}


def generate() -> None:
    rng = np.random.default_rng(SEED)
    months = _months()
    n = len(months)

    # --- Unemployment: mean-reverting around the decade natural rate, with cycles + shocks ---
    unemp = np.empty(n)
    level = _USTAR[1960]
    for i, m in enumerate(months):
        year = int(m[:4])
        ustar = _USTAR[_decade(year)]
        cycle = 1.4 * np.sin(2 * np.pi * i / 84.0)  # ~7yr business cycle
        level = level + 0.15 * (ustar - level) + 0.18 * cycle + rng.normal(0, 0.18)
        unemp[i] = float(np.clip(level, 3.2, 10.8))

    # --- Inflation (YoY %): Phillips relation vs u*, plus decade base and persistence ---
    infl = np.empty(n)
    prev = _BASE_INFL[1960]
    for i, m in enumerate(months):
        year = int(m[:4])
        d = _decade(year)
        target = _BASE_INFL[d] + _SLOPE[d] * (_USTAR[d] - unemp[i])
        prev = 0.7 * prev + 0.3 * target + rng.normal(0, 0.35)  # inflation is persistent
        infl[i] = float(np.clip(prev, -1.5, 15.0))

    # --- CPI index level reconstructed so that YoY(level) reproduces `infl` ---
    # First 12 months seeded; thereafter level[t] = level[t-12] * (1 + infl[t]/100).
    cpi = np.empty(n)
    base0 = 29.0
    for i in range(12):
        cpi[i] = base0 * (1 + 0.002 * i)
    for i in range(12, n):
        cpi[i] = cpi[i - 12] * (1 + infl[i] / 100.0)

    # --- Fed funds rate: loosely tracks inflation (a Taylor-ish rule) for the existing view ---
    ff = np.clip(1.0 + 1.2 * infl + 0.4 * (5.0 - unemp) + rng.normal(0, 0.3, n), 0.05, 20.0)

    OUT.mkdir(parents=True, exist_ok=True)

    # Introduce realistic messiness the cleaning step must handle:
    #  - a handful of missing CPI months (gaps)
    #  - CPI reported to 3dp, UNRATE to 1dp (different precisions)
    missing = set(rng.choice(np.arange(24, n - 24), size=9, replace=False).tolist())

    _write(OUT / "CPIAUCSL.csv", "CPIAUCSL", months, cpi, missing=missing, dp=3)
    _write(OUT / "UNRATE.csv", "UNRATE", months, unemp, dp=1)
    _write(OUT / "FEDFUNDS.csv", "FEDFUNDS", months, ff, dp=2)
    print(f"wrote {n} rows/series to {OUT} (CPIAUCSL missing {len(missing)} months by design)")


def _write(path: Path, col: str, months: list[str], values, missing=None, dp=2) -> None:
    missing = missing or set()
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", col])
        for i, m in enumerate(months):
            if i in missing:
                continue
            w.writerow([m, f"{values[i]:.{dp}f}"])


if __name__ == "__main__":
    generate()
