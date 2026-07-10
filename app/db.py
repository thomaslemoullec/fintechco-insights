"""SQLite access for the statements service.

Convention (see CLAUDE.md): parameterised queries only — never build SQL by
string formatting. Money is stored as integer cents.
"""
import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", "data/statements.db")
SCHEMA = Path(__file__).resolve().parent.parent / "migrations" / "001_init.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text())


def account_ids_for_customer(conn: sqlite3.Connection, customer_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT id FROM accounts WHERE customer_id = ?", (customer_id,)
    ).fetchall()
    return [r["id"] for r in rows]


def get_account(conn: sqlite3.Connection, account_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()


def get_customer(conn: sqlite3.Connection, customer_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()


def search_transactions(
    conn: sqlite3.Connection,
    account_id: int,
    start: str | None = None,
    end: str | None = None,
    merchant: str | None = None,
) -> list[sqlite3.Row]:
    # Parameterised filters — this part follows the convention.
    sql = "SELECT * FROM transactions WHERE account_id = ?"
    params: list[object] = [account_id]
    if start:
        sql += " AND posted_date >= ?"
        params.append(start)
    if end:
        sql += " AND posted_date <= ?"
        params.append(end)
    if merchant:
        sql += " AND merchant LIKE ?"
        params.append(f"%{merchant}%")
    sql += " ORDER BY posted_date DESC"
    return conn.execute(sql, params).fetchall()


def record_export(conn: sqlite3.Connection, customer_id: int, account_id: int, ts: str) -> None:
    # AC4 — every export is auditable (who, which account, when).
    conn.execute(
        "INSERT INTO statement_exports (customer_id, account_id, exported_at) VALUES (?, ?, ?)",
        (customer_id, account_id, ts),
    )
    conn.commit()
