# SETUP.md — the manual steps only you can do

Split into **Must do once** and **Optional**. Copy-paste commands. Your known values:

| Thing | Value |
|---|---|
| Jira site URL | `https://google-team-u5wj5df1.atlassian.net` |
| Jira cloud ID | `ce8b4631-0889-4880-a453-db85426b5ad8` |
| Jira project key | `SCRUM` (auto-generated; kept as-is) |
| Jira issue key | `SCRUM-6` (the demo ticket) |
| GitHub repo | `github.com/thomaslemoullec/fintechco-statements` |

---

## MUST DO ONCE

### 1. Anthropic / Claude Code
- Install Claude Code and sign in (API key on your paid plan, or Bedrock/Vertex).
- Nothing else needed — the harness (`CLAUDE.md`, `.claude/*`) ships in the repo.

### 2. Jira — project + ticket (already done)
1. Project **"FinTechCo"** exists, key **`SCRUM`** (the current "spaces" UI auto-generates keys;
   no rename needed — the demo uses whatever the key is).
2. The demo Story **SCRUM-6** ("Add Transaction Search & Export…") was created via the connector
   from `jira/TICKET.md`, with labels `payments`, `q3-roadmap`, `compliance-review`.
3. Keep **SCRUM-6** open in a browser tab for Beat 0.

### 3. Atlassian MCP — connect + OAuth (the #1 on-stage risk)
The repo ships `.mcp.json` declaring the `atlassian` server, so when you open Claude Code in
this folder it will offer to enable it — **approve it**. (Equivalent CLI, if you prefer:)
```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp
```
Then authenticate:
```
# inside Claude Code:
/mcp            # select "atlassian" → Authenticate → browser OAuth → approve
```
- Grant the account access it needs: **read issues + add comments** on the `SCRUM` project.
- Confirm it's live: `/mcp` should show `atlassian` connected, and `make demo-check` pings it.
- Re-run `/mcp` right before you present — an expired OAuth session is the classic failure.

### 4. GitHub — repo, push, branch protection  *(repo already created + pushed)*
```bash
gh auth login                       # or use a PAT
gh repo create fintechco-statements --public --source=. --remote=origin
git push -u origin main             # finished reference
git push origin demo-start          # the seeded starting branch
```
**Push protection note:** GitHub blocks the push because of the two seeded secrets (the fake
GCP SA key + the `sk_live_` Stripe key). They are intentional and fake — either click the
per-secret "allow" URLs GitHub prints, or disable **Settings → Code security → Secret
scanning → Push protection** for this demo repo.

Add the API key the CI security-review Action needs:
```bash
gh secret set ANTHROPIC_API_KEY     # paste your key when prompted
```
Then in the GitHub UI (Claude Code can't flip these): **Settings → Branches → Add branch
protection rule** for `demo-start` (the PR base during the demo) — and optionally `main`:
- ✅ Require a pull request before merging → **Require approvals: 1** (the human gate)
- ✅ Require status checks to pass before merging, and select as **required**:
  `tests (pytest)`, `lint (ruff)`, `secret scan (gitleaks)`, `IaC scan (tfsec)`,
  `SAST (semgrep)`, `Claude security review`
- ✅ Do not allow bypassing the above settings

During the demo you branch from `demo-start`, fix live, and open the PR **against
`demo-start`** (`gh pr create --base demo-start`). `main` is the fixed reference — don't
target it. (Optional: `gh repo edit --default-branch demo-start` if you'd rather PRs
default to it; the repo page will then show the seeded code, which the README flags.)

### 5. Local tooling + preflight
```bash
make setup          # venv + deps, registers .githooks, seeds the DB
```
Install the two Go-based scanners the hooks/CI use (pick your OS):
```bash
# macOS
brew install gitleaks tfsec
# Linux (binaries into ~/.local/bin)
mkdir -p ~/.local/bin
curl -sSL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz | tar -xz -C ~/.local/bin gitleaks
curl -sSL -o ~/.local/bin/tfsec https://github.com/aquasecurity/tfsec/releases/download/v1.28.11/tfsec-linux-amd64 && chmod +x ~/.local/bin/tfsec
```
Then verify:
```bash
make demo-check     # seeds present, control tests RED, scanners catch them, MCP reachable
```

---

## OPTIONAL
- **Bedrock / Vertex** instead of an API key: set `CLAUDE_CODE_USE_BEDROCK=1` (+ AWS creds/region)
  or `CLAUDE_CODE_USE_VERTEX=1` (+ GCP project/region). Narrated as the enterprise path.
- **`pre-commit` framework** instead of `.githooks`: `pip install pre-commit && pre-commit install`
  (uses `.pre-commit-config.yaml`).
- **Jira reset helper** (`scripts/jira_reset.py`): set `JIRA_SITE`, `JIRA_EMAIL`,
  `JIRA_API_TOKEN` (from id.atlassian.com → API tokens), `JIRA_ISSUE_KEY`.

---

## DO NOT
- ❌ Run the Terraform against a real GCP project — the IaC scans are static/offline only.
- ❌ Enable auto-merge — the human approval gate is part of the story.
- ❌ Commit or push `_internal/` — it holds your presenter script + the ticket seed-map.
  (It's git-ignored; double-check with `git status` before the first push.)
- ❌ "Fix" the seeded flaws before the demo — they must be present on `demo-start`.
