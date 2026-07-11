# FinTechCo statements service — demo Makefile.
# Boring and legible on purpose. `make help` lists targets.

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
export PATH := $(CURDIR)/$(VENV)/bin:$(HOME)/.local/bin:$(PATH)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(VENV): ## Create the virtualenv
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip

.PHONY: setup
setup: $(VENV) ## Install deps, register git hooks, seed the DB
	$(PIP) install --quiet -r requirements-dev.txt
	git config core.hooksPath .githooks
	@chmod +x .githooks/pre-commit .claude/hooks/*.sh 2>/dev/null || true
	$(MAKE) seed
	@echo "setup complete. (Install gitleaks + tfsec separately — see README.)"

.PHONY: seed
seed: ## (Re)seed the SQLite DB with fake data
	$(PY) scripts/seed_db.py

.PHONY: run
run: ## Run the API locally (http://127.0.0.1:8000)
	$(VENV)/bin/uvicorn app.main:app --reload

.PHONY: test
test: ## Run the full pytest suite
	$(PY) -m pytest

.PHONY: test-control
test-control: ## Run only the control tests (should be RED on demo-start)
	$(PY) -m pytest -m control

.PHONY: lint
lint: ## Ruff lint
	$(VENV)/bin/ruff check app tests scripts

.PHONY: scan
scan: ## Run the secret + IaC scanners
	gitleaks detect --no-git --source . --redact -v || true
	tfsec infra/terraform --no-color || true

.PHONY: reset
reset: ## Restore to pristine demo-start (local repo + generated files)
	./scripts/reset.sh

.PHONY: demo-check
demo-check: ## Assert the repo is demo-ready (seeds present, control tests red, tools + MCP)
	./scripts/preflight.sh
