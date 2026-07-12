"""Authentication for the statements service.

For the demo this is a thin stand-in for the real auth middleware: the caller's
identity arrives on the request (here via the `X-Customer-Id` header) and is made
available to handlers. In production this is your existing auth middleware / IdP —
the point that matters for the demo is that the *authenticated* caller identity is
available on the request context, so handlers have no excuse not to authorise.
"""
from fastapi import Header, HTTPException


class Caller:
    def __init__(self, customer_id: int):
        self.customer_id = customer_id


def get_current_caller(x_customer_id: str | None = Header(default=None)) -> Caller:
    if not x_customer_id:
        raise HTTPException(status_code=401, detail="missing authentication")
    try:
        return Caller(customer_id=int(x_customer_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid authentication") from None
