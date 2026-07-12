"""Transaction Search & Export (PAY ticket).

Endpoints:
  GET  /accounts/{account_id}/transactions          — search a customer's transactions
  POST /accounts/{account_id}/statements/export     — export a statement to the bucket
"""
import csv
import datetime
import io
import logging
import os
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import storage

from app import db
from app.auth import Caller, get_current_caller

logger = logging.getLogger("statements")

router = APIRouter()

STATEMENTS_BUCKET = os.environ.get("STATEMENTS_BUCKET", "fintechco-customer-statements")


def _to_amount(cents: int) -> str:
    # decimal money math (see CLAUDE.md) — never float
    return str((Decimal(cents) / Decimal(100)).quantize(Decimal("0.01")))


def _mask_account_number(number: str) -> str:
    return f"****{number[-4:]}"


def _ensure_owns_account(account, caller: Caller) -> None:
    if account["customer_id"] != caller.customer_id:
        raise HTTPException(status_code=403, detail="forbidden")


def _upload_statement(fname: str, content: str) -> None:
    # Goes straight to the CMEK-encrypted bucket — never persisted to local
    # disk in the clear.
    client = storage.Client()
    blob = client.bucket(STATEMENTS_BUCKET).blob(fname)
    blob.upload_from_string(content, content_type="text/csv")


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
        _ensure_owns_account(account, caller)

        logger.info(
            "Transactions searched for account %s by customer %s",
            _mask_account_number(account["account_number"]),
            caller.customer_id,
        )

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
        _ensure_owns_account(account, caller)

        logger.info(
            "Exporting statement for account %s requested by customer %s",
            _mask_account_number(account["account_number"]),
            caller.customer_id,
        )

        rows = db.search_transactions(conn, account_id)
        buf = io.StringIO()
        w = csv.writer(buf)
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

        ts = datetime.datetime.now(datetime.UTC).isoformat()
        fname = f"statement_{_mask_account_number(account['account_number'])}_{ts[:10]}.csv"
        _upload_statement(fname, buf.getvalue())

        db.record_export(conn, caller.customer_id, account_id, ts)

        return {"status": "exported", "bucket": STATEMENTS_BUCKET, "path": fname}
    finally:
        conn.close()
