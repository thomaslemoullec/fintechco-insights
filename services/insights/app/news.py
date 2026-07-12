"""Static financial-news items for the dashboard Home page.

Placeholder editorial content for the landing page (no external feed wired). Kept deterministic
and free of any personal/customer data.
"""
from __future__ import annotations

NEWS: list[dict] = [
    {
        "category": "Macro",
        "headline": "Labor market cools as unemployment ticks up to 4.2%",
        "source": "FinTechCo Research",
        "summary": "Payroll growth moderates; a softer print gives the Fed room to ease.",
    },
    {
        "category": "Rates",
        "headline": "Fed funds held at 3.6% — guidance turns data-dependent",
        "source": "FinTechCo Research",
        "summary": "The committee signals patience as core inflation drifts toward target.",
    },
    {
        "category": "Inflation",
        "headline": "Headline CPI eases; services prices remain sticky",
        "source": "FinTechCo Research",
        "summary": "Goods disinflation continues while shelter keeps core elevated.",
    },
    {
        "category": "Markets",
        "headline": "Rate-sensitive sectors rally on softer macro data",
        "source": "FinTechCo Research",
        "summary": "Duration bid returns as the growth-inflation mix shifts.",
    },
    {
        "category": "Research",
        "headline": "Is the Phillips curve back? Desk revisits the tradeoff",
        "source": "FinTechCo Research",
        "summary": "How the historical inflation-unemployment link has flattened.",
    },
]


def list_news() -> list[dict]:
    return NEWS
