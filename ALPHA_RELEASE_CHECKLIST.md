# Alpha Release Checklist

> **Purpose:** Verify that the EAIP platform meets all quality, security, and functionality gates required for an Alpha release.
> **Source:** Architecture audit — 33 verified findings resolved across 7 work packages.
> **Owner:** Subham Panigrahi (@subham1902)
> **Last updated:** 2026-07-11

---

## Instructions

Run this checklist after all 4 sprints (8 weeks) of Alpha stabilization work are complete. Every item must be checked and verified before declaring "Alpha Ready."

---

## Section 1: Security (All Critical Findings Resolved)

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 1.1 | JWT secret is not hard-coded in source | `grep -r "eaip-auth-secret-default" src/eaip/` returns empty | ☐ |
| 1.2 | JWT secret is configurable via `SecretProviderPort` or environment variable | Read `auth/tokens.py:__init__` — no default secret parameter | ☐ |
| 1.3 | `datapipeline/steps.py` no longer uses `exec()` | Grep `src/eaip/datapipeline/steps.py` for `exec(` | ☐ |
| 1.4 | `integration/transform.py` no longer uses `exec()` | Grep `src/eaip/integration/transform.py` for `exec(` | ☐ |
| 1.5 | `automation/executor.py` no longer uses `create_subprocess_shell` | Grep for `create_subprocess_shell` in `src/eaip/automation/` | ☐ |
| 1.6 | Bandit scan passes with zero medium+ findings | `make security` | ☐ |
| 1.7 | detect-secrets baseline has no new secrets | `detect-secrets scan --baseline .secrets.baseline` | ☐ |

---

## Section 2: Event Bus (All Events Delivered)

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 2.1 | `TokenService` publishes to `EventBus` | Read `auth/tokens.py` — `_emit()` body is not `pass` | ☐ |
| 2.2 | `AuthenticationService` publishes to `EventBus` | Read `auth/auth_providers.py` — `_emit()` body is not `pass` | ☐ |
| 2.3 | `apiext/caching.py` publishes cache events | Verify `CacheMiss`, `CacheHit`, `CacheInvalidated` are published | ☐ |
| 2.4 | `gateway/router.py` publishes endpoint lifecycle events | Verify `EndpointRegistered`, `EndpointUnregistered`, `ApiRequestProcessed` | ☐ |
| 2.5 | `sandbox/manager.py` publishes sandbox lifecycle events | Verify all 5 event types published | ☐ |
| 2.6 | `bluegreen/manager.py` publishes switch lifecycle events | Verify all 4 event types published | ☐ |
| 2.7 | `observability/slo.py` publishes SLO status events | Verify `SloStatusChanged`, `SloViolated` published | ☐ |
| 2.8 | `firewall/manager.py` publishes rule lifecycle events | Verify `RuleCreated`, `RuleUpdated`, `RuleDeleted`, `RuleSetActivated` | ☐ |
| 2.9 | `eventret/manager.py` publishes retention policy events | Verify `PolicyCreated` event published | ☐ |
| 2.10 | `xbridge/bridge.py` publishes connector lifecycle events | Verify `ConnectorRegistered`, `ConnectorUpdated`, `ConnectorDeleted` | ☐ |
| 2.11 | `collaboration/coordinator.py:_publish()` awaits the event bus call | Verify `_publish` is `async def` and contains `await` | ☐ |
| 2.12 | Single event dispatch pattern exists across the platform | No custom `_emit()`/`_event_callback` patterns remain | ☐ |

---

## Section 3: Error Handling

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 3.1 | Zero `except Exception: pass` in production code | `grep -rn "except.*:.*pass" src/eaip/` returns empty | ☐ |
| 3.2 | `audit/store.py` uses `asyncio.create_task()` not `ensure_future()` | Read `audit/store.py` | ☐ |
| 3.3 | Event error classes have distinct `ErrorCode` values | Read `events/errors.py` | ☐ |

---

## Section 4: Async Correctness

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 4.1 | `gateway/rate_limiter.py` uses `asyncio.Lock()` | Read `gateway/rate_limiter.py` | ☐ |
| 4.2 | `schema/registry.py` uses `asyncio.Lock()` | Read `schema/registry.py` | ☐ |
| 4.3 | `sdk/clients.py` no longer uses `anyio.from_thread.run()` | Read `sdk/clients.py` | ☐ |
| 4.4 | `sdk/manager.py` no longer uses `anyio.from_thread.run()` | Read `sdk/manager.py` | ☐ |

---

## Section 5: Time & Data Hygiene

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 5.1 | Zero `datetime.now()` (naive) in collaboration packages | `grep -rn "datetime.now()" src/eaip/collaboration/` returns empty | ☐ |
| 5.2 | Token storage has TTL-based eviction | Read `auth/tokens.py` for eviction logic | ☐ |
| 5.3 | `shared/types.py:Bytes` alias renamed or removed | Read `shared/types.py` | ☐ |
| 5.4 | `compliance/framework.py:108` dead code removed | Read `compliance/framework.py` | ☐ |
| 5.5 | `events/dispatcher.py` accesses bus via public API | Read `events/dispatcher.py:150` | ☐ |

---

## Section 6: Stub Implementation

| # | Check | Verification Method | Status |
|---|-------|---------------------|--------|
| 6.1 | `S3ArchiveStore` is implemented or removed | Read `archive/store.py` | ☐ |
| 6.2 | At least one deployment strategy has implementation | Read `deploy/deployer.py` | ☐ |
| 6.3 | CLI `run_forever()` reads and executes input | Read `cli/shell.py` | ☐ |

---

## Section 7: Quality Gates

| # | Check | Command | Status |
|---|-------|---------|--------|
| 7.1 | All tests pass | `pytest tests/ -q` exits 0 | ☐ |
| 7.2 | Test coverage ≥ 85% | `pytest --cov=src --cov-report=term` | ☐ |
| 7.3 | mypy strict passes | `mypy --strict src/` exits 0 | ☐ |
| 7.4 | ruff check passes | `ruff check src/` exits 0 | ☐ |
| 7.5 | ruff format check passes | `ruff format --check src/` exits 0 | ☐ |
| 7.6 | Bandit passes | `bandit -c pyproject.toml -r src/` exits 0 | ☐ |
| 7.7 | pip-audit passes | `pip-audit --strict` exits 0 | ☐ |
| 7.8 | Pre-commit passes | `pre-commit run --all-files` exits 0 | ☐ |
| 7.9 | Package builds cleanly | `python -m build` succeeds | ☐ |
| 7.10 | Docker image builds | `docker build .` succeeds | ☐ |

---

## Section 8: Documentation

| # | Check | Status |
|---|-------|--------|
| 8.1 | `MASTER_AUDIT.md` — verified findings up to date | ☐ |
| 8.2 | `ALPHA_BACKLOG.md` — all completed items marked done | ☐ |
| 8.3 | `ALPHA_ROADMAP.md` — status updated | ☐ |
| 8.4 | `SPRINT_PLAN.md` — retrospectives captured | ☐ |
| 8.5 | `CHANGELOG.md` — Alpha release entry added | ☐ |
| 8.6 | `RISK_REGISTER.md` — any new risks documented | ☐ |
| 8.7 | `DECISION_REGISTER.md` — any new decisions captured | ☐ |
| 8.8 | `SECURITY.md` — updated with known Alpha limitations | ☐ |

---

## Final Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | Subham Panigrahi | | ☐ |
| Security Reviewer | | | ☐ |
| QA Lead | | | ☐ |

---

*When all checkboxes are checked, the platform is **Alpha Ready**.*
