"""Transaction search tests, including the AC1 authorisation control test."""
import pytest


def test_customer_can_list_own_transactions(client):
    r = client.get("/accounts/1/transactions", headers={"X-Customer-Id": "1"})
    assert r.status_code == 200
    assert len(r.json()["transactions"]) == 2


def test_missing_auth_is_rejected(client):
    r = client.get("/accounts/1/transactions")
    assert r.status_code == 401


@pytest.mark.control
def test_customer_cannot_read_another_accounts_transactions(client):
    # AC1: Alice (customer 1) must not read Bob's account (2). Expect 403.
    # RED on demo-start (seeded IDOR serves it with 200); GREEN after the fix.
    r = client.get("/accounts/2/transactions", headers={"X-Customer-Id": "1"})
    assert r.status_code == 403
