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
def test_phillips_endpoint_exposes_disclosures(client):
    """The client-facing view endpoint must return provenance + disclosures, not just data."""
    body = client.get("/api/views/phillips").json()
    for key in ("as_of", "sources", "methodology", "disclaimer", "decade_stats", "points",
                "then", "now", "decisions", "ab_variants"):
        assert body.get(key), f"missing {key}"


def test_ab_event_accepts_known_and_rejects_unknown(client):
    assert client.post("/api/ab/event", json={"variant": "by-decade"}).json() == {"ok": True}
    assert client.post("/api/ab/event", json={"variant": "bogus"}).status_code == 400
