---
name: test-gen
description: Generate pytest tests for the statements service — especially authorisation/compliance control tests that are written and committed BEFORE the implementation (TDD). Use when adding or changing an endpoint that touches account data or exports.
---

# test-gen

Write tests **first**, commit them, then implement. Tests live in `tests/` and use the
`client` fixture from `tests/conftest.py` (a deterministic seeded DB: customer 1 "Alice
Rivera" owns account 1; customer 2 "Bob Chen" owns account 2).

## Always include these control tests for account-data endpoints
Mark them `@pytest.mark.control` so `make demo-check` can assert they fail before the fix.

1. **Authorisation (AC1 / CWE-639):** a caller cannot read or export an account they do
   not own — expect `403`. Use customer 1 requesting account 2.
2. **No NPI in logs (AC3 / CWE-532):** capture logs with `caplog` and assert the full
   account number and customer name do **not** appear.
3. **Infra controls (AC2):** assert the statements bucket Terraform uses a CMEK
   (`default_kms_key_name`) and has no `allUsers`/`allAuthenticatedUsers` binding.

## Conventions
- One behaviour per test; clear names (`test_customer_cannot_export_another_accounts_statement`).
- Assert status codes explicitly.
- Money is integer cents in the DB; assert on formatted decimal strings.
- Do not weaken a test to make it pass — fix the code. Commit tests before implementation
  so any later change to a test is visible in the diff.
