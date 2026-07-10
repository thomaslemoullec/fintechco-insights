# PAY — Transaction Search & Export (Jira ticket source)

> Reference copy of the ticket the demo opens on. Paste this into your Jira project to
> create the Story (Beat 3 reads it via the Atlassian MCP; Beat 13 comments back on it).
> Suggested type: Story. Suggested labels: `payments`, `q3-roadmap`, `compliance-review`.

---

**Summary:** Add Transaction Search & Export to the customer statements service

**Epic / Component:** Payments — Statements
**Priority:** High
**Reporter:** Priya N. (Product Manager, Payments)
**Assignee:** _(unassigned)_

---

## Description

Support and Ops keep asking for a faster way to pull a customer's transaction history when
handling disputes and reconciliation requests. Today they file a data request and wait — it
can take a day.

We want a self-serve endpoint in the statements service that lets an authenticated customer
(and, later, an authorised support agent acting on their behalf) **search their transactions
and export them as a statement** (CSV/PDF) that we drop in the statements bucket and return a
link to.

This is the first slice: the authenticated-customer path. The support-agent-on-behalf-of path
is a follow-up ticket.

### In scope
- `GET /accounts/{account_id}/transactions` — search/filter a customer's own transactions (by date range, amount, merchant).
- `POST /accounts/{account_id}/statements/export` — generate a statement file, store it, return a signed link.
- Store exported statements in the existing GCS statements bucket.

### Out of scope
- The support-agent delegated-access path (separate ticket).
- Any change to the ledger rounding logic — that module is legacy and owned elsewhere; do not touch it as part of this ticket.

---

## Acceptance criteria

- [ ] **AC1 — Authorisation:** a customer can only search and export transactions **for accounts they own**. A request for an account the caller does not own must be rejected (403), not served. This must be covered by tests.
- [ ] **AC2 — Data protection in transit and at rest:** exported statements contain non-public personal information (NPI). Files at rest in the statements bucket must be **encrypted with our customer-managed key (CMEK)**, and access to the bucket must follow **least privilege** — only the statements service identity may read/write.
- [ ] **AC3 — No sensitive data in logs:** request/response logging for these endpoints must **not** write full account numbers or customer names. Use masked identifiers.
- [ ] **AC4 — Auditable:** every export is recorded (who, which account, when) for the audit trail.
- [ ] **AC5 — Tested:** unit + integration tests, including negative/authorisation tests, pass in CI. Security and IaC scans are green. A reviewer has approved.

---

## Notes for the implementer
- Follow the service conventions in `CLAUDE.md` (definition of done = tests + review + security scans pass).
- The statements bucket and its IAM live in the Terraform for this service.
- Ship behind the existing auth middleware; the authenticated caller's identity is available on the request context.

---

## Definition of done
- All acceptance criteria met and demonstrably tested.
- CI green (tests + SAST/SCA + secret scan + IaC scan) and a human approver has signed off.
- Ticket updated with what shipped, the tests added, and any issues found and fixed.
