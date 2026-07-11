# DEMO.md — operator run-sheet

Beat-by-beat, cross-referenced to `_internal/FinTechCo_Demo_RunBook_v7.md`. For each beat:
the exact thing you type, what the room sees, rough time, the one-line **Say**, the
**▶ Exec so-what**, and the **Fallback**. Full narration + persona Q&A live in the runbook.

> **Before you start:** `make demo-check` is green, and you've run `/mcp` in Claude Code to
> confirm the Atlassian OAuth is live. The demo ticket is `SCRUM-6`.
> Minimum core if short on time: **2 → 3 → 4 → 5 → 7 → 9 → 10 → 12**.

---

## Beat 0 — Open on the ticket (bridge from slide 3)
- **Do:** switch to the browser tab showing the Jira ticket (SCRUM-6).
- **Say:** *"The fastest way to make an agent better on your codebase is not a smarter model — it's a tighter feedback loop. Let me show you what that means on one real ticket."*
- **Fallback:** the ticket tab is already open; nothing to fail here.

## Beat 1 — Your banking controls + settings hierarchy · ~60s · setup
- **Do:** show the harness files: `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/compliance-reviewer.md`, `.claude/skills/`, `.claude/hooks/`. Then prove a control live:
  - Prompt: *"Read the file infra/terraform/statements-exporter-sa-key.json"* → the **deny-rule refuses it** (settings.json denies `Read(./infra/terraform/*-key.json)`).
- **Say:** *"`CLAUDE.md` is context — the conventions Claude follows. `settings.json` is control — deny-rules and hooks enforced outside the model. And they layer: this repo ships its own controls; above them your platform team's managed policy overrides anything a developer sets."*
- **▶ Exec so-what:** "Your security policy stops being a PDF nobody reads and becomes something enforced automatically on every engineer's machine." (Platform/Infra + CTO)
- **Fallback:** if the deny prompt misbehaves, open `.claude/settings.json` and read the `deny` block aloud.

## Beat 2 — Understand the code + document the legacy ledger · ~75s · LOCAL
- **Do:** `/output-style explanatory`, then:
  *"Explore the payments service and walk me through how a transaction flows through it. The ledger module is legacy and undocumented — kick off a subagent to document it and draw a diagram while we keep working."* then `/output-style default`.
- **Aside (live):** *"Who last changed the ledger's rounding logic, and why?"* → Claude answers from real git history (**Priya Nair, 2021 — switched allocation to largest-remainder to fix recon batch 7**).
- **Say:** *"It pulls only the files it needs into context — that's how it scales to your monorepo."*
- **▶ Exec so-what:** "That undocumented module a senior engineer is scared to touch — understood and documented in the background. Onboarding and key-person risk, both down." (Head of DT)
- **Fallback:** `git log --follow app/ledger/rounding.py` shows the same history if the subagent is slow.

## Beat 3 — Pull the ticket via MCP · ~40s · LOCAL
- **Do:** *"Read Jira ticket SCRUM-6 through the Atlassian connector and give me the requirements and acceptance criteria in your own words."*
- **Then:** `/permissions` (or `/mcp`) — show Jira is allowlisted, read is allowed, **write tools stay gated**.
- **Say:** *"Claude reaches only the servers you allow, and within a server only the tools you permit — reading the ticket here, not writing to Jira. Every call is `mcp__server__tool`, its own allow/ask/deny decision."*
- **▶ Exec so-what:** "We start where your business starts — a ticket in Jira — and we'll close that same ticket at the end." (Head of DT + PMO)
- **Fallback (do NOT fake it):** read the ticket from the open browser tab and narrate the write-back; `jira/TICKET.md` is the offline read-only copy.

## Beat 4 — Plan first, let it interview you · ~60s · LOCAL
- **Do:** enter plan mode →
  *"Before any code, read the search and export paths and give me a plan — what changes, the flow, what could break. Ask me about anything ambiguous or risky."* Answer its question; edit the plan with Ctrl+G.
- **Reveal:** *"The plan already assumes parameterised queries, decimal amounts, an authz check, and an encrypted export — I never asked. Those are our rules from `CLAUDE.md`; they load every session."*
- **▶ Exec so-what:** "It plans before it codes and asks clarifying questions — the discipline of a senior hire, not a black box." (CTO + Head of DT)
- **Fallback:** if plan mode stalls, show a pre-written plan and talk through it.

## Beat 5 — TDD: write the control tests first (the trap) · ~55s · LOCAL
- **Do:** *"Write the tests first and commit them — including one that a customer cannot retrieve another account's transactions, and one that exported statements have no NPI in logs and are encrypted at rest. Don't implement yet. Run them."*
- **Show:** the control tests **fail red** against the seeded code: `make test-control` → 5 failing.
- **Say:** *"I commit the tests first, so if it ever alters a test to pass, the diff shows it. That red authorization test **is** the vulnerability — a customer seeing another's transactions is a reportable breach, caught before a line ships."*
- **▶ Exec so-what:** "The rule that protects customers — 'you can only see your own accounts' — is a test written before the feature. Compliance becomes executable." (CTO + PMO)
- **Fallback:** the tests already exist on `demo-start`; just run `make test-control` and narrate.

## Beat 6 — Implement to green · ~60s · LOCAL
- **Do:** *"Now implement against these tests until they pass. Also update the Terraform to add the statements bucket."*
- **Show:** edits land; the **PostToolUse lint hook** runs on each edit (self-corrects); checkpoints auto-save; app-level tests go green.
- **Say:** *"Conventions applied, checks on every edit, and it checkpoints before each change so I can `/rewind` instantly. For this money path I'm supervising closely."*
- **▶ Exec so-what:** "Fast is the boring part now — which is exactly why we can afford to spend our time on verification." (Head of DT)
- **Fallback:** if an edit misfires, `/rewind` to the last checkpoint.

## Beat 7 — Local compliance review, app + cloud (the climax) · ~75s · LOCAL
- **Do:** *"Use the compliance-reviewer subagent to review all the changes — application and infrastructure — against our controls before we commit."*
- **Show:** the **read-only** reviewer returns findings in regulatory language: IDOR/CWE-639 → GLBA exposure; NPI in a log; bucket no-CMEK + over-broad IAM + exported SA key. Open `.claude/agents/compliance-reviewer.md` for 2s — "Read and Grep only. It can only report."
- **Say:** *"Findings in your examiner's language — GLBA, PCI, least privilege — and they complement your deterministic scanners, they don't replace them."*
- **▶ Exec so-what (slowly):** "It just caught a bug that would let one customer download another customer's bank statements — a reportable breach — before a single line was committed. And it costs nothing to run this on every change." (whole room)
- **Fallback:** `make scan` (gitleaks + tfsec) plus `SEEDS.md` gives the same findings deterministically.

## Beat 8 — Fix and re-verify · ~45s · LOCAL
- **Do:** *"Fix the authorization gap, remove the NPI from logs, add CMEK on the bucket, tighten the IAM binding, and switch to Workload Identity Federation instead of a key. Then re-run the tests and the review."*
- **Show:** control tests red → green (`make test`); a clean review; briefly `/rewind`.
- **Say:** *"You ship a loop, not a prompt — and `/rewind` takes the code back to any checkpoint."*
- **▶ Exec so-what:** "The finding didn't just get flagged — it got fixed and proven fixed, in the same loop." (CTO)
- **Fallback:** `main` holds the fully-fixed reference to diff against.

## Beat 9 — Commit: deterministic gates fire · ~35s · PRE-COMMIT
- **Do:** *"Commit this."*
- **Show:** the pre-commit hook runs **ruff + gitleaks + tfsec**. gitleaks **blocks the planted secret** → move it to Secret Manager / env → commit succeeds.
- **Say:** *"Fast, deterministic gates at commit time — the secret never left the machine, the infra change was policy-scanned before it was even committed. These are shell hooks outside the model: zero tokens, deterministic, and they can't be talked out of."*
- **▶ Exec so-what:** "Two independent safety nets already, and we haven't left the laptop." (Platform/Infra + CTO)
- **Fallback:** run `.githooks/pre-commit` manually to show the block, then remove the secret and re-run.

## Beat 10 — Open a PR: full CI + AI review + human gate · ~50s · CI
- **Do:** *"Open a pull request with a clear summary and the security notes."*
  The PR base is **`demo-start`** (the seeded state), so the diff is your fix and CI has
  something to check: `gh pr create --base demo-start --fill` (or set base in the UI).
  *(`main` is the already-fixed reference — don't target it, the diff would be empty.)*
- **Show:** required checks side-by-side — **tests / ruff / gitleaks / tfsec / semgrep / Claude security review** — under **branch protection**: no merge without all green **and a human approver**.
- **Say:** *"An independent security pass on every change, and a human owns the merge — that's your SOX change-control, approved and evidenced."*
- **▶ Exec so-what:** "Your change-control regime, automated: nothing merges without checks passing and a named human approving — evidence captured for examiners." (CTO + Platform/Infra)
- **Note (live-runnable):** the security-review Action runs on your own repo. Only caveat is CI latency.
- **Fallback:** show an already-run PR if API/CI is slow.

## Beat 11 — Deploy: gated, in your cloud · ~25s · CI (narrated)
- **Say:** *"Cloud Build → Cloud Deploy → GKE/Cloud Run with Binary Authorization on GCP; the equivalent CodePipeline on AWS. Local → commit → CI → deploy, in your tenancy, image-verified. Nothing leaves your cloud, on Bedrock or Vertex."*
- **Fallback:** narrated only — no live deploy (see runbook ⚠ personal-account note).

## Beat 12 — Audit trail + cost · ~30s
- **Do:** `cat audit.log` (the hook's local, attributable trail) and `/cost`.
- **Say:** *"Locally, a hook logs every tool call. In your tenancy the same events stream to your SIEM via OpenTelemetry, correlated by session, redacted by default — your examiner evidence."*
- **▶ Exec so-what:** "Everything you just watched is measurable — adoption, cycle time, cost per change, findings caught." (PMO + Head of DT)
- **Fallback:** `audit.log` is real; the admin dashboard is narrated (org-scoped).

## Beat 13 — Close the loop · ~20s
- **Do:** *"Update Jira ticket SCRUM-6 via the Atlassian connector with a comment: what shipped, the tests added, and the two issues we caught and fixed (the IDOR and the cloud-encryption gap). Start the comment with 'Claude Code demo close-out'."*
- **Say:** *"A PM's ticket goes in, a resolved ticket comes back."*
- **▶ Exec so-what / close:** hand to slide 8 (measure) and slide 9 (pilot). See the runbook's exec close.
- **Fallback:** if the MCP write fails, narrate it against the open ticket tab; run `python scripts/jira_reset.py` later to clean up.

---

## After each run — reset
```bash
make reset          # local repo back to demo-start (seeds restored), DB reseeded
# then clean Jira:  python scripts/jira_reset.py   (deletes the 'Claude Code demo close-out' comment)
make demo-check     # confirm green before the next run
```

## The 30-second data-science grace note (say it, don't build it)
See the runbook — same governed tool, a quant goes CSV → cleaned data → model → shared
Artifacts page that never lets the data leave your boundary.
