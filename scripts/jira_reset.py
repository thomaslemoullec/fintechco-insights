"""Delete the demo's closing comment(s) from the Jira ticket so the next run is clean.

This is a FALLBACK cleanup helper (the demo itself reads/writes the ticket via the
Atlassian MCP connector). It uses the Jira REST API with a personal API token.

Set these env vars (see SETUP.md), then run `python scripts/jira_reset.py`:
  JIRA_SITE       e.g. https://google-team-u5wj5df1.atlassian.net
  JIRA_EMAIL      the Atlassian account email
  JIRA_API_TOKEN  a token from https://id.atlassian.com/manage-profile/security/api-tokens
  JIRA_ISSUE_KEY  e.g. PAY-1

Only comments containing the marker below are deleted, so it won't touch real comments.
"""
import base64
import json
import os
import urllib.error
import urllib.request

MARKER = "Claude Code demo close-out"


def _req(method: str, url: str, token_header: str, data: bytes | None = None):
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", token_header)
    r.add_header("Accept", "application/json")
    if data is not None:
        r.add_header("Content-Type", "application/json")
    return urllib.request.urlopen(r, timeout=15)


def main() -> None:
    site = os.environ.get("JIRA_SITE", "").rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    issue = os.environ.get("JIRA_ISSUE_KEY", "")
    if not all([site, email, token, issue]):
        raise SystemExit(
            "Set JIRA_SITE, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_ISSUE_KEY (see SETUP.md)."
        )

    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    header = f"Basic {auth}"
    base = f"{site}/rest/api/3/issue/{issue}/comment"

    try:
        with _req("GET", base, header) as resp:
            comments = json.load(resp).get("comments", [])
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Jira API error {e.code}: {e.read().decode()[:200]}") from None

    deleted = 0
    for c in comments:
        body = json.dumps(c.get("body", {}))
        if MARKER in body:
            with _req("DELETE", f"{base}/{c['id']}", header):
                deleted += 1
    print(f"Deleted {deleted} demo comment(s) from {issue}.")


if __name__ == "__main__":
    main()
