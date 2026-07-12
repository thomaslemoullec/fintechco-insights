"""API contract tests for the dashboard endpoints."""
import pytest


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_indicators_lists_known_series(client):
    ids = {i["id"] for i in client.get("/api/indicators").json()["indicators"]}
    assert {"UNRATE", "INFLATION", "FEDFUNDS"} <= ids


def test_series_ok_and_unknown(client):
    ok = client.get("/api/series/INFLATION")
    assert ok.status_code == 200
    body = ok.json()
    assert body["as_of"] and body["points"]
    assert client.get("/api/series/NOPE").status_code == 404


@pytest.mark.control
def test_phillips_endpoint_exposes_disclosures(client):
    """The client-facing view endpoint must return provenance + disclosures, not just data."""
    body = client.get("/api/views/phillips").json()
    for key in ("as_of", "sources", "methodology", "disclaimer", "decade_correlations", "points"):
        assert body.get(key), f"missing {key}"
