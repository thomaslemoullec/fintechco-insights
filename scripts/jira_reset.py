"""Reset the demo Jira ticket to its clean starting state.

Deletes the demo close-out comment(s) and moves the issue back to "To Do". Best-effort:
if credentials aren't set it prints a hint and exits 0 (so `make rehearse` never fails on it).

Auth (one-time): create a Jira API token at https://id.atlassian.com/manage-profile/security/api-tokens
then export:
    export JIRA_EMAIL=you@example.com
    export JIRA_API_TOKEN=xxxx
Optional overrides: JIRA_BASE (site URL), JIRA_ISSUE (default SCRUM-7).

Run: `make jira-reset`  (also invoked by `make rehearse`).
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("JIRA_BASE", "https://google-team-u5wj5df1.atlassian.net").rstrip("/")
ISSUE = os.environ.get("JIRA_ISSUE", "SCRUM-7")
EMAIL = os.environ.get("JIRA_EMAIL")
TOKEN = os.environ.get("JIRA_API_TOKEN")
MARKER = "Claude Code close-out"  # the close-out comment must start with this (see DEMO.md)
TARGET_STATUS = "To Do"


def _req(method: str, path: str, body: dict | None = None) -> dict | None:
    auth = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}/rest/api/3{path}", data=data, method=method)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (trusted host)
        raw = resp.read()
        return json.loads(raw) if raw else None


def main() -> int:
    if not (EMAIL and TOKEN):
        print("  jira-reset: skipped (set JIRA_EMAIL + JIRA_API_TOKEN to auto-reset the ticket)")
        return 0
    try:
        # 1) delete the demo close-out comment(s)
        comments = _req("GET", f"/issue/{ISSUE}/comment")["comments"]
        removed = 0
        for c in comments:
            if MARKER.lower() in json.dumps(c.get("body", "")).lower():
                _req("DELETE", f"/issue/{ISSUE}/comment/{c['id']}")
                removed += 1

        # 2) move back to To Do (if not already there)
        transitions = _req("GET", f"/issue/{ISSUE}/transitions")["transitions"]
        match = next((t for t in transitions if t["to"]["name"].lower() == TARGET_STATUS.lower()), None)
        if match:
            _req("POST", f"/issue/{ISSUE}/transitions", {"transition": {"id": match["id"]}})
            moved = f"→ {TARGET_STATUS}"
        else:
            moved = f"(already {TARGET_STATUS} or no transition)"
        print(f"  jira-reset: {ISSUE} — deleted {removed} close-out comment(s); status {moved}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"  jira-reset: skipped (HTTP {e.code} — check token/permissions)")
        return 0
    except Exception as e:  # noqa: BLE001 - never fail the rehearsal reset
        print(f"  jira-reset: skipped ({type(e).__name__})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
