---
name: ui-check
description: Fast headless-browser sanity check of the Macro Insights dashboard — loads the real page with Playwright/Chromium and checks it actually renders, instead of the generic browser-driven fallback.
---

# ui-check

Loads the dashboard in headless Chromium (Playwright) and checks it renders for real —
mount points filled, as-of date populated, no console/page errors. This is the browser this
project uses; don't fall back to a different tool.

Playwright + Chromium live in the project venv (`requirements-dev.txt`). If `playwright`
import fails or `~/.cache/ms-playwright` is empty, run once:
```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install --with-deps chromium
```

## Steps
1. **Start the server** if not already up: `make dev` in the background, poll
   `http://127.0.0.1:8000/api/indicators` until it responds. If you started it, stop it when
   done.
2. **Run the check** with `.venv/bin/python3`, using `playwright.sync_api`:
   - `page.goto("http://127.0.0.1:8000/", wait_until="networkidle")`
   - Collect `console` (type `"error"`) and `pageerror` events — any hit is a fail.
   - `page.wait_for_selector("#view-root:not(:empty)", timeout=5000)` — the SPA mounted and
     rendered indicator content, not just the empty shell.
   - `#asof-date` inner text is non-empty — the data as-of date reached the DOM.
   - `#error-banner` is hidden — the app didn't hit its own error path.
3. Report pass/fail per check, one line each. A timeout on `#view-root` filling, a non-empty
   error banner, or any console/page error is a fail.

## What this does not cover
Visual/layout regressions and design-token compliance (see `web/DESIGN.md`) still need a
screenshot review or a human look — call that out rather than claiming visual coverage this
skill doesn't have.
