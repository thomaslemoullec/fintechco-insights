"""API contract tests for the dashboard endpoints."""


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
    body = ok.json()
    assert body["as_of"] and body["points"]
    assert body["methodology"] and body["disclaimer"]
    assert client.get("/api/series/NOPE").status_code == 404


def test_phillips_curve_view(client):
    res = client.get("/api/views/phillips-curve")
    assert res.status_code == 200
    body = res.json()
    assert body["as_of"] and body["sources"] and body["methodology"] and body["disclaimer"]
    assert body["points"]
    point = body["points"][0]
    assert {"date", "inflation", "unemployment", "decade"} <= point.keys()
