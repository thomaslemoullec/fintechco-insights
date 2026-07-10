"""Statement export tests: AC1 (authorisation) and AC3 (no NPI in logs)."""
import logging

import pytest


def test_customer_can_export_own_statement(client):
    r = client.post("/accounts/1/statements/export", headers={"X-Customer-Id": "1"})
    assert r.status_code == 200
    assert r.json()["status"] == "exported"


@pytest.mark.control
def test_customer_cannot_export_another_accounts_statement(client):
    # AC1: Alice (1) must not export Bob's account (2). Expect 403.
    # RED on demo-start; GREEN after the ownership check is added.
    r = client.post("/accounts/2/statements/export", headers={"X-Customer-Id": "1"})
    assert r.status_code == 403


@pytest.mark.control
def test_no_npi_in_logs(client, caplog):
    # AC3: exporting must not write full account numbers or customer names to logs.
    # RED on demo-start (seeded logs both at INFO); GREEN once logging is masked.
    with caplog.at_level(logging.INFO, logger="statements"):
        r = client.post("/accounts/1/statements/export", headers={"X-Customer-Id": "1"})
    assert r.status_code == 200
    logged = " ".join(rec.getMessage() for rec in caplog.records)
    assert "4000000000000001" not in logged, "full account number leaked to logs"
    assert "Alice Rivera" not in logged, "customer name leaked to logs"
