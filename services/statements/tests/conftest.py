"""Test fixtures. Builds a small, deterministic seeded DB per test.

  customer 1 "Alice Rivera" owns account 1 (4000000000000001)
  customer 2 "Bob Chen"     owns account 2 (4000000000000002)
"""
import pytest
from fastapi.testclient import TestClient


def _seed() -> None:
    from app import db

    conn = db.get_connection()
    db.init_schema(conn)
    conn.executemany(
        "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
        [(1, "Alice Rivera", "alice.rivera@example.com"), (2, "Bob Chen", "bob.chen@example.com")],
    )
    conn.executemany(
        "INSERT INTO accounts (id, account_number, customer_id, kind) VALUES (?, ?, ?, ?)",
        [(1, "4000000000000001", 1, "checking"), (2, "4000000000000002", 2, "savings")],
    )
    conn.executemany(
        "INSERT INTO transactions (account_id, posted_date, amount_cents, merchant, description) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (1, "2025-01-05", -1299, "Coffee Bar", "latte"),
            (1, "2025-01-06", 250000, "ACME Payroll", "salary"),
            (2, "2025-01-05", -4599, "Book Shop", "novel"),
            (2, "2025-01-07", -1000, "City Transit", "fare"),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def _stub_gcs_upload(monkeypatch):
    # Tests never hit real GCS/credentials — the upload boundary is stubbed the
    # same way the DB path is, below.
    from app import transactions

    monkeypatch.setattr(transactions, "_upload_statement", lambda fname, content: None)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", str(tmp_path / "test.db"))
    _seed()
    from app.main import app

    return TestClient(app)
