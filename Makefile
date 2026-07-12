VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(VENV): ## Create the virtualenv
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

setup: $(VENV) ## Install dependencies and seed fixtures
	$(PIP) install -q -r requirements-dev.txt
	$(PY) scripts/gen_fixtures.py

fetch: ## Refresh the FRED series cache from the live API (needs FRED_API_KEY)
	$(PY) scripts/fetch_fred.py

seed: ## Generate synthetic FRED fixtures (offline fallback, deterministic)
	$(PY) scripts/gen_fixtures.py

dev: ## Run the app (API + dashboard UI) at http://127.0.0.1:8000
	$(VENV)/bin/uvicorn app.main:app --reload --app-dir services/insights

run: dev ## Alias for `dev`

test: ## Run the full test suite
	$(VENV)/bin/pytest

test-control: ## Run only the data-governance / model-risk control tests
	$(VENV)/bin/pytest -m control

lint: ## Lint the Python code
	$(VENV)/bin/ruff check services scripts
