"""Data-governance / model-risk tests for the FRED data source layer.

The @pytest.mark.control tests guard provenance (every series pull must be traceable —
series id, row count, as-of date) and secrecy (the API key must never be observable in a
log line or exception message) per CLAUDE.md > Data governance / Secrets.
"""
import logging

import httpx
import pytest
from app.fred import FredClient


@pytest.mark.control
def test_get_series_logs_provenance(caplog):
    """Every pull must emit a log line naming the series, row count and as-of date."""
    client = FredClient()
    with caplog.at_level(logging.INFO, logger="insights.fred"):
        df = client.get_series("UNRATE")

    assert caplog.records, "get_series() did not emit a provenance log record"
    record = caplog.records[-1].getMessage()
    assert "UNRATE" in record
    assert str(len(df)) in record
    as_of = df["DATE"].max().date().isoformat()
    assert as_of in record


@pytest.mark.control
def test_failed_fetch_never_exposes_api_key(monkeypatch, caplog):
    """A failed live request must not leak api_key via its exception message or logs.

    httpx.HTTPStatusError/.RequestError embed the full request URL (query string and
    all) in their message — since FRED only accepts api_key as a query param, that
    string must never reach a raised exception or a log record.
    """
    secret = "super-secret-fred-key"
    client = FredClient(api_key=secret)
    client.live = True

    def boom(*args, **kwargs):
        request = httpx.Request("GET", "https://api.stlouisfed.org/x", params=kwargs.get("params"))
        response = httpx.Response(500, request=request)
        raise httpx.HTTPStatusError("server error", request=request, response=response)

    monkeypatch.setattr(httpx, "get", boom)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(RuntimeError) as excinfo:
            client.get_series("CPIAUCSL")

    assert secret not in str(excinfo.value)
    assert secret not in "".join(r.getMessage() for r in caplog.records)


def test_httpx_transport_logging_is_silenced():
    """httpx's own INFO-level request logging (which includes the URL) must be disabled."""
    assert logging.getLogger("httpx").level >= logging.WARNING
