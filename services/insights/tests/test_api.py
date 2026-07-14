"""API contract tests for the dashboard endpoints."""
import pytest


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_news(client):
    news = client.get("/api/news").json()["news"]
    assert news and all("headline" in n for n in news)


def test_indicators_lists_known_series(client):
    ids = {i["id"] for i in client.get("/api/indicators").json()["indicators"]}
    assert {"UNRATE", "INFLATION", "FEDFUNDS"} <= ids


def test_series_ok_and_unknown(client):
    ok = client.get("/api/series/INFLATION")
    assert ok.status_code == 200
    assert ok.json()["as_of"] and ok.json()["points"]
    assert client.get("/api/series/NOPE").status_code == 404


@pytest.mark.control
def test_inflation_unemployment_view(client):
    """SCRUM-7 — written before the endpoint exists (TDD); implement to make it pass.

    Reuses analysis.build_frame(), which already aligns inflation/unemployment monthly
    and drops unpaired months — no new transform, just a thin endpoint over it.
    """
    resp = client.get("/api/views/inflation-unemployment")
    assert resp.status_code == 200
    body = resp.json()
    assert body["as_of"]
    assert body["disclaimer"]
    assert body["points"], "must return paired inflation/unemployment points"
    assert all(
        "date" in p and "inflation" in p and "unemployment" in p for p in body["points"]
    ), "every point must carry both series — no unpaired months"
