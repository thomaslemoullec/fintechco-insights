---
name: test-gen
description: Generate pytest tests for the Macro Insights service — especially data-governance / model-risk control tests that are written and committed BEFORE the implementation (TDD). Use when adding or changing a data pull, a transform, or a client-facing view.
---

# test-gen

Write tests **first**, commit them, then implement. Tests live in
`services/insights/tests/` and run against the committed **synthetic** FRED fixtures
(`services/insights/app/data/*.csv`) — deterministic input, so results are reproducible.

## Always include these control tests
Mark them `@pytest.mark.control` so `make test-control` can assert they fail before the fix.

1. **Reproducibility / determinism (model risk · SR 11-7):** run a cleaning/analysis
   transform twice on the same fixture and assert the outputs are identical (same input →
   same output). No hidden randomness.
2. **Provenance / as-of present in client-facing views (data governance · SR 11-7):**
   assert every client-facing view/figure carries the **data as-of date**, a
   **methodology note**, and a **disclaimer** — a figure missing any of these is not
   shippable.
3. **Source attribution (data governance):** assert each series/indicator carries its
   source (e.g. "U.S. BLS via FRED"), preserved from ingestion through to the view.
4. **No secrets (CWE-798):** assert `FRED_API_KEY` / credentials are read from the
   environment, never hardcoded in source.

## Conventions
- One behaviour per test; clear names
  (`test_phillips_view_carries_asof_source_and_disclaimer`).
- Assert explicitly — status codes for API tests, exact fields for view/provenance tests.
- Prefer the synthetic fixtures; do not hit the live FRED API in tests.
- Do not weaken a test to make it pass — fix the code. Commit tests before implementation
  so any later change to a test is visible in the diff.
