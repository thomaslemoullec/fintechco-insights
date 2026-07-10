"""Transaction Search & Export (PAY ticket).

Endpoints:
  GET  /accounts/{account_id}/transactions          — search a customer's transactions
  POST /accounts/{account_id}/statements/export     — export a statement to the bucket

NOTE FOR THE DEMO: this file ships with deliberately planted flaws on the
`demo-start` branch (marked `# DEMO-SEED`). They are caught live and fixed during
the demo. See SEEDS.md. Do not "clean them up" outside the demo flow.
"""
import csv
import datetime
import logging
import os
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.auth import Caller, get_current_caller

logger = logging.getLogger("statements")

router = APIRouter()

# DEMO-SEED 4 (planted secret / CWE-798): a hardcoded credential in source. The
# pre-commit secret scan (gitleaks) blocks this at commit time (Beat 9). The fix
# is to read it from the environment / Secret Manager.
STATEMENTS_SIGNING_KEY = "sk_live_4eC39HqLyjWDarjtT1zdp7dc0aB1cD2eF3gH"

STATEMENTS_BUCKET = os.environ.get("STATEMENTS_BUCKET", "fintechco-customer-statements")
EXPORT_DIR = os.environ.get("EXPORT_DIR", "exports")


def _to_amount(cents: int) -> str:
    # decimal money math (see CLAUDE.md) — never float
    return str((Decimal(cents) / Decimal(100)).quantize(Decimal("0.01")))


@router.get("/accounts/{account_id}/transactions")
def search_account_transactions(
    account_id: int,
    start: str | None = None,
    end: str | None = None,
    merchant: str | None = None,
    caller: Caller = Depends(get_current_caller),
):
    conn = db.get_connection()
    try:
        account = db.get_account(conn, account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="account not found")

        # DEMO-SEED 1 (IDOR / BOLA, CWE-639): the handler serves transactions for
        # `account_id` taken straight from the URL and NEVER checks that the account
        # belongs to `caller.customer_id`. Any authenticated customer can read any
        # account's transactions. Violates AC1. The fix is an ownership check → 403.
        rows = db.search_transactions(conn, account_id, start, end, merchant)
        return {
            "account_id": account_id,
            "transactions": [
                {
                    "id": r["id"],
                    "posted_date": r["posted_date"],
                    "amount": _to_amount(r["amount_cents"]),
                    "merchant": r["merchant"],
                    "description": r["description"],
                }
                for r in rows
            ],
        }
    finally:
        conn.close()


@router.post("/accounts/{account_id}/statements/export")
def export_statement(
    account_id: int,
    caller: Caller = Depends(get_current_caller),
):
    conn = db.get_connection()
    try:
        account = db.get_account(conn, account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="account not found")
        customer = db.get_customer(conn, account["customer_id"])

        # DEMO-SEED 1 (IDOR / BOLA, CWE-639): same missing ownership check on export —
        # any customer can export any account's statement. Violates AC1.

        # DEMO-SEED 2 (NPI in logs, CWE-532): logs the FULL account number and the
        # customer's name at INFO. Statement data is NPI. Violates AC3. The fix is to
        # log a masked identifier only (e.g. last 4).
        logger.info(
            "Exporting statement for account %s (%s) requested by customer %s",
            account["account_number"],
            customer["name"],
            caller.customer_id,
        )

        rows = db.search_transactions(conn, account_id)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        fname = f"statement_{account['account_number']}_{ts[:10]}.csv"
        fpath = os.path.join(EXPORT_DIR, fname)
        with open(fpath, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["posted_date", "amount", "merchant", "description"])
            for r in rows:
                w.writerow(
                    [
                        r["posted_date"],
                        _to_amount(r["amount_cents"]),
                        r["merchant"],
                        r["description"],
                    ]
                )

        db.record_export(conn, caller.customer_id, account_id, ts)

        # "upload" to the statements bucket + return a signed link. The signature uses
        # the hardcoded key above (DEMO-SEED 4).
        signed = f"https://storage.googleapis.com/{STATEMENTS_BUCKET}/{fname}?sig={STATEMENTS_SIGNING_KEY[:12]}"
        return {"status": "exported", "bucket": STATEMENTS_BUCKET, "url": signed}
    finally:
        conn.close()
