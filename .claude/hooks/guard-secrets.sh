#!/usr/bin/env bash
# PreToolUse guard — blocks any tool call that would read/expose a secret or
# credential, regardless of the tool used. The settings.json deny-rule already
# blocks the Read tool on secret paths; this hook enforces the same policy for
# the shell (and anything else), so the control lives on the RESOURCE, not one
# tool — and is enforced outside the model.
#
# Contract: PreToolUse hook. Exit 2 = block the tool call (stderr is surfaced
# to Claude). Exit 0 = allow.
input=$(cat)

# Secret/credential path patterns. Kept targeted to avoid false positives.
secret_re='\.env([^a-zA-Z]|$)|-key\.json|/secrets/|id_rsa|\.pem|credentials\.json'

if printf '%s' "$input" | grep -Eq "$secret_re"; then
  echo "BLOCKED by security policy: access to secrets/credentials is not permitted (CLAUDE.md > Secrets). Secrets live in Secret Manager (fred-api-key), never in files or shell reads." >&2
  exit 2
fi
exit 0
