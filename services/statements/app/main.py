"""FinTechCo statements service — FastAPI app.

Run locally: `make run` (uvicorn app.main:app --reload).
"""
import logging

from fastapi import FastAPI

from app.transactions import router as transactions_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(title="FinTechCo Statements Service", version="0.1.0")
app.include_router(transactions_router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
