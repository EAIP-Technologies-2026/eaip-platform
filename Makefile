# =============================================================================
# EAIP — Makefile
# -----------------------------------------------------------------------------
# Standard developer tasks. Run `make help` for an overview.
# Requires: GNU Make 4+, Python 3.11+, git.
# =============================================================================

SHELL          := /usr/bin/env bash
.SHELLFLAGS    := -eu -o pipefail -c
.DEFAULT_GOAL  := help
MAKEFLAGS      += --no-print-directory --warn-undefined-variables

# ---- Configurable variables (override on the command line) -------------------
PY             ?= python3
VENV           ?= .venv
VENV_BIN       := $(VENV)/bin
PIP            := $(VENV_BIN)/pip
PYTHON         := $(VENV_BIN)/python
RUFF           := $(VENV_BIN)/ruff
BLACK          := $(VENV_BIN)/black
MYPY           := $(VENV_BIN)/mypy
PYTEST         := $(VENV_BIN)/pytest
PRECOMMIT      := $(VENV_BIN)/pre-commit
PIP_AUDIT      := $(VENV_BIN)/pip-audit
BANDIT         := $(VENV_BIN)/bandit

SRC_DIRS       := src tests

# ---- Internal --------------------------------------------------------------
# Local override file for personal aliases / paths (git-ignored)
-include local.mk

# Colour helpers (TTY-safe)
ifeq ($(shell test -t 1 && echo tty),tty)
  CYAN   := \033[36m
  YELLOW := \033[33m
  GREEN  := \033[32m
  RED    := \033[31m
  BOLD   := \033[1m
  RESET  := \033[0m
else
  CYAN   :=
  YELLOW :=
  GREEN  :=
  RED    :=
  BOLD   :=
  RESET  :=
endif

.PHONY: help
help: ## Show this help.
	@printf "$(BOLD)EAIP — developer tasks$(RESET)\n\n"
	@awk 'BEGIN {FS = ":.*?## "} \
	      /^[a-zA-Z0-9_.-]+:.*?## / { \
	         printf "  $(CYAN)%-18s$(RESET) %s\n", $$1, $$2 \
	      }' $(MAKEFILE_LIST)
	@printf "\nOverride variables: e.g. \`make test PYTEST_ARGS='-k token'\`\n"

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
$(VENV)/bin/activate:
	@printf "$(CYAN)→ Creating virtualenv at $(VENV)$(RESET)\n"
	@$(PY) -m venv $(VENV)
	@$(PIP) install --upgrade pip wheel setuptools

.PHONY: bootstrap
bootstrap: $(VENV)/bin/activate ## Create venv, install dev deps, install hooks.
	@printf "$(CYAN)→ Installing project (dev + test)$(RESET)\n"
	@$(PIP) install -e ".[dev,test]"
	@printf "$(CYAN)→ Installing pre-commit hooks$(RESET)\n"
	@$(PRECOMMIT) install --install-hooks
	@$(PRECOMMIT) install --hook-type commit-msg
	@printf "$(GREEN)✓ Environment ready. Activate with: source $(VENV_BIN)/activate$(RESET)\n"

.PHONY: deps-update
deps-update: ## Recompile and update locked dev/test dependencies.
	@$(PIP) install --upgrade pip wheel setuptools
	@$(PIP) install --upgrade -e ".[dev,test]"

# -----------------------------------------------------------------------------
# Formatting & Linting
# -----------------------------------------------------------------------------
.PHONY: fmt
fmt: ## Auto-format the codebase (black + ruff --fix).
	@$(BLACK) $(SRC_DIRS) || true
	@$(RUFF) check --fix $(SRC_DIRS) || true
	@$(RUFF) format $(SRC_DIRS) || true

.PHONY: fmt-check
fmt-check: ## Verify formatting without writing changes.
	@$(BLACK) --check $(SRC_DIRS)
	@$(RUFF) format --check $(SRC_DIRS)

.PHONY: lint
lint: ## Run linters (ruff).
	@$(RUFF) check $(SRC_DIRS)

.PHONY: typecheck
typecheck: ## Run mypy --strict.
	@$(MYPY) $(SRC_DIRS)

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
PYTEST_ARGS ?=

.PHONY: test
test: ## Run the test suite with coverage.
	@$(PYTEST) --cov --cov-report=term-missing --cov-report=xml $(PYTEST_ARGS)

.PHONY: test-fast
test-fast: ## Run only fast unit tests (no coverage).
	@$(PYTEST) -m "unit and not slow" --no-cov $(PYTEST_ARGS)

.PHONY: test-parallel
test-parallel: ## Run tests in parallel using pytest-xdist.
	@$(PYTEST) -n auto $(PYTEST_ARGS)

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
.PHONY: audit
audit: ## Run dependency vulnerability scan.
	@$(PIP_AUDIT) --strict

.PHONY: bandit
bandit: ## Run static security analysis (bandit).
	@$(BANDIT) -c pyproject.toml -r src

.PHONY: security
security: audit bandit ## Run all security scans.

# -----------------------------------------------------------------------------
# Aggregate gates
# -----------------------------------------------------------------------------
.PHONY: check
check: fmt-check lint typecheck test ## Run all CI gates locally.
	@printf "$(GREEN)✓ All checks passed$(RESET)\n"

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks against every file.
	@$(PRECOMMIT) run --all-files

# -----------------------------------------------------------------------------
# Developer experience
# -----------------------------------------------------------------------------
.PHONY: health
health: ## Read-only repository health check.
	@bash scripts/healthcheck.sh

.PHONY: validate
validate: ## Local pre-flight (lint + format + typecheck + test) with friendly output.
	@bash scripts/validate.sh

.PHONY: validate-docs
validate-docs: ## Walk Markdown files, verify internal links and required docs.
	@bash scripts/validate-docs.sh

.PHONY: diagnostics
diagnostics: ## Print an environment snapshot suitable for bug reports.
	@bash scripts/diagnostics.sh

.PHONY: docker-dev
docker-dev: ## Build & enter the local dev container (requires docker).
	@docker compose -f docker-compose.dev.yml run --rm eaip

.PHONY: docker-test
docker-test: ## Run the test suite inside the dev container.
	@docker compose -f docker-compose.dev.yml run --rm eaip make test

# -----------------------------------------------------------------------------
# Hygiene
# -----------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove caches, build artefacts, and coverage data.
	@find . -type d \( \
	     -name __pycache__ \
	  -o -name .pytest_cache \
	  -o -name .mypy_cache \
	  -o -name .ruff_cache \
	  -o -name .hypothesis \
	  -o -name htmlcov \
	  -o -name build \
	  -o -name dist \
	  -o -name "*.egg-info" \
	\) -prune -exec rm -rf {} +
	@rm -f .coverage .coverage.* coverage.xml
	@printf "$(GREEN)✓ Cleaned$(RESET)\n"

.PHONY: distclean
distclean: clean ## Remove the virtualenv as well.
	@rm -rf $(VENV)
	@printf "$(GREEN)✓ Virtualenv removed$(RESET)\n"

# -----------------------------------------------------------------------------
# Meta
# -----------------------------------------------------------------------------
.PHONY: version
version: ## Print the package version.
	@$(PYTHON) -c "import importlib.metadata as m; print(m.version('eaip'))" 2>/dev/null \
	   || grep '^version' pyproject.toml | head -1 | cut -d '"' -f2
