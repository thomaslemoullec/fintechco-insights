"""Seed the statements DB with FAKE data only (faker). No real PII, ever.

Deterministic (fixed seed) so the demo and the control tests are reproducible:
  - customer 1  "Alice Rivera"   owns account 1  (acct number 4000000000000001)
  - customer 2  "Bob Chen"       owns account 2  (acct number 4000000000000002)
  plus a handful of random fake customers/accounts.

Run: `python scripts/seed_db.py`  (or `make seed`).
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker  # noqa: E402

from app import db  # noqa: E402

fake = Faker("en_US")
Faker.seed(42)
random.seed(42)


def _tx_rows(account_id: int, n: int) -> list[tuple]:
    rows = []
    for _ in range(n):
        d = fake.date_between(start_date="-180d", end_date="today").isoformat()
        cents = random.randint(-250_00, 500_00)
        rows.append((account_id, d, cents, fake.company(), fake.bs()[:40]))
    return rows


def main() -> None:
    os.makedirs(os.path.dirname(db.DB_PATH) or ".", exist_ok=True)
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    conn = db.get_connection()
    db.init_schema(conn)

    # Fixed customers/accounts the control tests rely on.
    conn.executemany(
        "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
        [
            (1, "Alice Rivera", "alice.rivera@example.com"),
            (2, "Bob Chen", "bob.chen@example.com"),
        ],
    )
    conn.executemany(
        "INSERT INTO accounts (id, account_number, customer_id, kind) VALUES (?, ?, ?, ?)",
        [
            (1, "4000000000000001", 1, "checking"),
            (2, "4000000000000002", 2, "savings"),
        ],
    )

    # A few extra random fake customers/accounts for realism.
    next_cust, next_acct = 3, 3
    for _ in range(6):
        conn.execute(
            "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
            (next_cust, fake.name(), fake.email()),
        )
        conn.execute(
            "INSERT INTO accounts (id, account_number, customer_id, kind) VALUES (?, ?, ?, ?)",
            (next_acct, fake.numerify("40############"), next_cust, "checking"),
        )
        next_cust += 1
        next_acct += 1

    tx: list[tuple] = []
    for acct in range(1, next_acct):
        tx.extend(_tx_rows(acct, 25))
    conn.executemany(
        "INSERT INTO transactions (account_id, posted_date, amount_cents, merchant, description) "
        "VALUES (?, ?, ?, ?, ?)",
        tx,
    )
    conn.commit()

    counts = {
        "customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        "accounts": conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
        "transactions": conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
    }
    conn.close()
    print(f"Seeded {db.DB_PATH}: {counts}")


if __name__ == "__main__":
    main()
