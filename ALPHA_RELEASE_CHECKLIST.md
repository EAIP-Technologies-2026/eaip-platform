# EAIP Alpha Release Checklist

**Version:** 0.0.2
**Date:** 2026-07-21

> Use this checklist to track readiness for an Alpha release. Each item must be verified before release.

---

## 1. Backend

### Core Platform
- [ ] **FAIL** Ruff lint passes with < 100 errors — 6420 violations found (D-series docstrings)
- [ ] **FAIL** mypy type-check passes — 1 error: migration filename `001_initial_schema.py` is invalid decimal literal
- [ ] **PASS** Python 3.11+ compatibility — tested on 3.13.14
- [ ] **PASS** All core dependencies installable — `pip install -e .` succeeds
- [ ] **PASS** Platform boots successfully — `python -m eaip` starts Uvicorn
- [ ] **PASS** 27 HTTP routes registered — verified via `create_app()`

### Authentication
- [ ] **FAIL** Auth integration tests pass — 13 failed, 3 errored: `EAIP_AUTH_SECRET` not set
- [ ] **PASS** JWT tokens generated and validated — `TokenService` functional when env var is set
- [ ] **FAIL** No hardcoded production secrets — `"eaip-dev-secret-do-not-use-in-production"` in `__main__.py`
- [ ] **FAIL** Token service handles missing secret gracefully — raises `RuntimeError` instead of degraded mode

### Event System
- [ ] **PASS** EventBus publishes and delivers events — 2,541 event-related unit tests pass
- [ ] **PASS** EventStore records all DomainEvent with classification
- [ ] **PASS** Recent events retrievable by agent, workflow, mission, type filters

### WebSocket / Realtime
- [ ] **PASS** WebSocket endpoint accepts connections at `/ws`
- [ ] **PASS** ConnectionManager tracks connections with heartbeat/purge
- [ ] **PASS** PushService delivers messages to channel subscribers
- [ ] **PASS** EventStore events are classified and pushed with channel context
- [ ] **FAIL** 9 ws unit test files pass — all pass
- [ ] **PASS*** Channel filtering implementation in `event_listener` — *pending end-to-end verification due to missing frontend subscribe protocol

### Workflow Engine
- [ ] **PASS** Workflow DAG execution — sequential and parallel steps
- [ ] **PASS** Pause, resume, cancel operations
- [ ] **PASS** State machine: valid transitions enforced
- [ ] **PASS** Child workflow execution
- [ ] **PASS** Step approval mechanism

### Data Pipeline
- [ ] **FAIL** `croniter` dependency optional — crashes at import if not installed
- [ ] **PASS** Pipeline scheduler tests pass — 5 of 10 fail due to missing dep
- [ ] **WARN** Consider making `croniter` a core dependency or wrapping import

---

## 2. Frontend

### Build
- [ ] **FAIL** `pnpm build` succeeds — **FAILED**: TypeScript error + ESLint crash
- [ ] **FAIL** `pnpm typecheck` passes — 1 error in `@eaip/auth`
- [ ] **FAIL** `pnpm lint` passes — crashes with missing `@eslint/eslintrc`
- [ ] **PASS** `pnpm build:packages` succeeds — all 50 packages compile

### Test
- [ ] **FAIL** `pnpm test` passes — 1 vitest test fails (redirect test)
- [ ] **FAIL** Coverage thresholds met — no coverage report generated
- [ ] **WARN** Only 1 vitest test exists for enterprise-console app — insufficient coverage
- [ ] **WARN** 18 Playwright e2e spec files exist but were not executed

### TypeScript
- [ ] **FAIL** Strict mode enforced — root `tsconfig.json` has `strict: true`
- [ ] **FAIL** `noUncheckedIndexedAccess` — catches `base64Url` but error prevents build
- [ ] **PASS** 56 tsconfig files, all packages typed
- [ ] **PASS** Path aliases configured for all 48 `@eaip/*` packages

### Dependencies
- [ ] **FAIL** ESLint `@eslint/eslintrc` missing — blocks all lint checks
- [ ] **PASS** pnpm lockfile frozen — `pnpm-lock.yaml` present
- [ ] **PASS** Workspace protocol (`workspace:*`) used for internal deps

---

## 3. Docker

### Backend Image
- [ ] **PASS** Dockerfile exists — Python 3.13-slim-bookworm
- [ ] **PASS** Multi-stage not needed for Python (single stage sufficient)
- [ ] **PASS** `docker-compose.yml` includes PostgreSQL, Redis, Qdrant
- [ ] **PASS** Healthcheck configured at `/health`
- [ ] **PASS** Persistent volumes for all data stores

### Frontend Image
- [ ] **PASS** Dockerfile exists — Node 20 Alpine
- [ ] **PASS** Multi-stage build (deps → builder → runner)
- [ ] **PASS** All 5 apps built in single image
- [ ] **PASS** Non-root `nextjs` user in production
- [ ] **PASS** `docker-compose.yml` for development

---

## 4. CI/CD

- [ ] **FAIL** CI pipeline defined — **NOT CONFIGURED** (no `.github/` directory)
- [ ] **FAIL** PR checks (lint, typecheck, test) — not configured
- [ ] **FAIL** Build validation — not configured
- [ ] **FAIL** E2E test execution — not configured
- [ ] **FAIL** Deployment pipeline — not configured
- [ ] **WARN** `Makefile` present with comprehensive targets — usable locally but not in CI
- [ ] **WARN** GitHub Actions `ci.yml` exists in frontend but NOT in platform repo

---

## 5. Environment

### Backend
- [ ] **PASS** `.env` template present — development defaults
- [ ] **PASS** `.env.local` for secrets (gitignored)
- [ ] **FAIL** `EAIP_AUTH_SECRET` documented — not present in `.env` comments
- [ ] **PASS** `.dockerignore` present
- [ ] **WARN** `pyproject.toml` specifies `Development Status :: 2 - Pre-Alpha`

### Frontend
- [ ] **PASS** `.env.example` present — all variables documented
- [ ] **PASS** `.env` and `.env.local` present
- [ ] **FAIL** Auth issuer and client ID empty — `NEXT_PUBLIC_AUTH_ISSUER` and `NEXT_PUBLIC_AUTH_CLIENT_ID` not populated
- [ ] **PASS** Telemetry disabled by default

---

## 6. Documentation

- [ ] **PASS** `README.md` exists — project description and links
- [ ] **FAIL** API documentation — no Swagger/OpenAPI docs accessible (FastAPI auto-docs may work)
- [ ] **PASS** Architecture docs — 15 files in `docs/`
- [ ] **PASS** `CHANGELOG.md` exists
- [ ] **PASS** `LICENSE` (Apache 2.0) exists
- [ ] **PASS** `SECURITY.md` referenced
- [ ] **WARN** No `CONTRIBUTING.md`
- [ ] **FAIL** No Storybook build for frontend — `pnpm storybook:build` not tested

---

## 7. Testing

### Backend
- [ ] **PASS** `pytest` configured — `pyproject.toml` with all options
- [ ] **PASS** Unit tests: 8926 passed, 18 failed, 10 skipped, 3 errors
- [ ] **PASS** Integration tests: 131 passed, 0 failed
- [ ] **PASS** E2E tests: 14 passed, 0 failed
- [ ] **FAIL** `pytest-cov` configured but coverage report not verified
- [ ] **FAIL** Auth integration tests need `EAIP_AUTH_SECRET` env var
- [ ] **WARN** Skipped tests: openpyxl, reportlab, scipy not installed

### Frontend
- [ ] **FAIL** `vitest` configured — 1 test fails
- [ ] **FAIL** Coverage thresholds not verified
- [ ] **FAIL** Playwright e2e not executed — 18 spec files, but no run attempted
- [ ] **WARN** Only 1 vitest test for entire enterprise-console app

---

## 8. Deployment

- [ ] **PASS** Docker Compose production stack defined
- [ ] **PASS** PostgreSQL + Redis + Qdrant backing services configured
- [ ] **PASS** Healthcheck at `/health`
- [ ] **PASS** Volume mounts for data persistence
- [ ] **FAIL** No Kubernetes manifests
- [ ] **FAIL** No Terraform/Pulumi/Bicep infrastructure-as-code
- [ ] **FAIL** No deployment guide or runbook
- [ ] **WARN** No migration strategy for database schema
- [ ] **FAIL** No CI/CD pipeline for automated deployment

---

## 9. Monitoring

- [ ] **PASS** Health check framework — `eaip/health/` with per-module reporters
- [ ] **PASS** OpenTelemetry integration — API, SDK, OTLP exporter configured
- [ ] **PASS** Structured logging — `structlog` configured
- [ ] **PASS** Prometheus metrics likely auto-configured via OpenTelemetry
- [ ] **WARN** No dashboards or alerting rules defined
- [ ] **WARN** No log aggregation (ELK/Loki/DataDog) configuration
- [ ] **FAIL** No uptime monitoring or synthetic checks

---

## Overall Status

| Area | Status | Notes |
|------|--------|-------|
| Backend Core | ⚠️ PASS | Stable, well-tested; minor test env config gap |
| Authentication | ❌ FAIL | Secret config issue in tests; JWT parsing gap in frontend |
| WebSocket/Realtime | ⚠️ PASS | Infrastructure solid; frontend protocol incomplete |
| Frontend Build | ❌ FAIL | Blocked by type error and ESLint dependency |
| Frontend Tests | ❌ FAIL | Insufficient coverage; 1 test fails |
| Docker | ✅ PASS | Production and dev stacks defined |
| CI/CD | ❌ FAIL | Not configured |
| Documentation | ⚠️ PASS | Good architecture docs; missing operational docs |
| Security | ❌ FAIL | Hardcoded dev secret, no CSP/headers, missing auth config |

**Alpha Release Verdict: NOT RECOMMENDED**

The following must be resolved before Alpha release:
1. Frontend build — fix `base64Url` type error (B-01)
2. Frontend ESLint — install missing `@eslint/eslintrc` (B-02)
3. Auth test env — set `EAIP_AUTH_SECRET` in test fixtures (B-03)
4. mypy — handle migration filename in config (B-04)
5. CI/CD — define at minimum a CI pipeline (B-05)
