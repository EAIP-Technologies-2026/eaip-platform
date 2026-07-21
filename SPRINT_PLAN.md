# Sprint Plan — Alpha Stabilization

> **Duration:** 8 weeks, 4 two-week sprints
> **Start:** 2026-07-14
> **End:** 2026-09-05
> **Velocity estimate:** 5-8 story points per sprint (1 SP ≈ 1 engineering day)

---

## Sprint 1: Security Hardening (Jul 14 - Jul 25)

**Focus:** WP-01 — Eliminate all Critical vulnerabilities

### Sprint Goal
Resolve all 4 Critical findings from the architecture audit. Make the platform safe to deploy in any environment without immediate RCE or account-takeover risk.

### Backlog Items

| ID | Task | Effort (SP) | Owner | Dependencies |
|----|------|-------------|-------|-------------|
| S1-01 | **JWT secret remediation** — remove hard-coded default from `TokenService.__init__`; integrate with `SecretProviderPort` | 2 | TBD | None |
| S1-02 | **Data pipeline exec replacement** — replace `exec(script_code, exec_globals, local_context)` with AST-based restricted evaluation or declarative transform DSL | 2 | TBD | None |
| S1-03 | **Integration transform exec replacement** — replace `exec(script_source, {"__builtins__": {}}, local_vars)` with safe alternative | 1 | TBD | S1-02 (share approach) |
| S1-04 | **Shell injection fix** — replace `create_subprocess_shell(action.target)` with `create_subprocess_exec()` and explicit argument array | 1 | TBD | None |

### Sprint Review Checklist
- [ ] `make security` passes (bandit + pip-audit)
- [ ] No new `mypy --strict` errors
- [ ] All existing 8,967+ tests pass with no regressions
- [ ] New unit tests for each security fix

### Risks
- S1-02/03: Replacing `exec()` in data pipeline may break existing pipeline definitions. Mitigation: Add integration tests before changing implementation.

---

## Sprint 2: Event Bus Reliability (Jul 28 - Aug 8)

**Focus:** WP-02 — Make event delivery work end-to-end

### Sprint Goal
All domain events are actually delivered to subscribers. Auth events, collaboration events, and 8 packages with orphaned events are wired to `EventBus`.

### Backlog Items

| ID | Task | Effort (SP) | Owner | Dependencies |
|----|------|-------------|-------|-------------|
| S2-01 | **Wire auth events** — `TokenService._emit()` → `EventBus.publish()`; `AuthenticationService._emit()` → `EventBus.publish()` | 1 | TBD | Sprint 1 completion |
| S2-02 | **Fix apiext/caching.py** — publish `CacheMiss`, `CacheHit`, `CacheInvalidated` to EventBus | 0.5 | TBD | None |
| S2-03 | **Fix gateway/router.py** — publish `EndpointRegistered`, `EndpointUnregistered`, `ApiRequestProcessed` | 0.5 | TBD | None |
| S2-04 | **Fix sandbox/manager.py** — publish all sandbox lifecycle events | 1 | TBD | None |
| S2-05 | **Fix bluegreen/manager.py** — publish all deployment switch events | 1 | TBD | None |
| S2-06 | **Fix observability/slo.py** — publish `SloStatusChanged`, `SloViolated` | 0.5 | TBD | None |
| S2-07 | **Fix firewall/manager.py** — publish rule lifecycle events | 0.5 | TBD | None |
| S2-08 | **Fix eventret/manager.py** — publish retention policy events | 0.5 | TBD | None |
| S2-09 | **Fix xbridge/bridge.py** — publish connector lifecycle events | 0.5 | TBD | None |
| S2-10 | **Fix collaboration coordinator** — make `_publish()` async and `await` the event bus call | 0.5 | TBD | None |
| S2-11 | **Consolidate dispatch patterns** — migrate `_emit()`/`_event_callback` patterns in `agent_governance/`, `features/`, `license/`, `floatlicense/` to `EventBus` | 2 | TBD | S2-01..S2-10 |
| S2-12 | **Integration test** — verify auth event end-to-end flow | 1 | TBD | S2-01 |

### Sprint Review Checklist
- [ ] All 8 orphaned-event packages publish to EventBus
- [ ] Collaboration events are delivered
- [ ] Single event dispatch pattern across the platform
- [ ] Auth event end-to-end test passes
- [ ] All existing tests pass

---

## Sprint 3: Error Handling & Async Correctness (Aug 11 - Aug 22)

**Focus:** WP-03, WP-04, WP-05

### Sprint Goal
Eliminate all silent error swallowing. Fix async/threading violations. Standardize time handling and add token eviction.

### Backlog Items

| ID | Task | Effort (SP) | Owner | Dependencies |
|----|------|-------------|-------|-------------|
| S3-01 | **Bare except audit** — fix all 71+ `except Exception: pass` instances across 40+ files | 3 | TBD | None |
| S3-02 | **Audit store fix** — replace `asyncio.ensure_future()` with `asyncio.create_task()` and tracked task list | 1 | TBD | None |
| S3-03 | **Event error codes** — assign distinct `ErrorCode` values to `EventError`, `EventHandlerError`, `EventPublishError`, `EventRetryExhaustedError` | 0.5 | TBD | None |
| S3-04 | **Rate limiter lock** — replace `threading.Lock()` with `asyncio.Lock()` | 0.5 | TBD | None |
| S3-05 | **Schema registry lock** — replace `threading.Lock()` with `asyncio.Lock()` | 0.5 | TBD | None |
| S3-06 | **SDK async fix** — convert synchronous SDK methods to `async def` or replace `anyio.from_thread.run()` with proper async bridge | 1 | TBD | None |
| S3-07 | **UTC datetime audit** — replace `datetime.now()` with `utc_now()` in `collaboration/coordinator.py` and `collaboration/delegation.py` | 0.5 | TBD | None |
| S3-08 | **Token eviction** — add TTL-based garbage collection to `TokenService` | 1 | TBD | S3-07 |
| S3-09 | **Type shadowing fix** — rename or remove `Bytes` alias in `shared/types.py` | 0.5 | TBD | None |
| S3-10 | **Compliance dead code** — remove or fix line 108 in `compliance/framework.py` | 0.5 | TBD | None |
| S3-11 | **Dispatcher encapsulation fix** — add public API to `EventBus` to avoid private attribute access | 1 | TBD | None |

### Sprint Review Checklist
- [ ] Zero `except Exception: pass` in `src/eaip/`
- [ ] `make typecheck` passes
- [ ] `make test` passes with no regressions
- [ ] Token eviction test verified

---

## Sprint 4: Stubs & Polish (Aug 25 - Sep 5)

**Focus:** WP-06, WP-07

### Sprint Goal
Complete or remove all stub implementations. Fix minor code quality issues. Prepare Alpha release candidate.

### Backlog Items

| ID | Task | Effort (SP) | Owner | Dependencies |
|----|------|-------------|-------|-------------|
| S4-01 | **S3ArchiveStore** — implement with `boto3` or replace with documented `NotImplementedError` referencing tracking issue | 1 | TBD | None |
| S4-02 | **Deployment strategies** — implement at least `_rolling_deploy` via subprocess; document others | 2 | TBD | None |
| S4-03 | **CLI shell fix** — wire `run_forever()` to call `execute()` on each input line | 1 | TBD | None |
| S4-04 | **Compliance framework fix** — access `RegulationMapper` controls through public API | 0.5 | TBD | None |
| S4-05 | **Import hygiene** — move `import re` etc. to module top level | 0.5 | TBD | None |
| S4-06 | **Alpha release verification** — run full `make check`, `make security`, `make test` | 1 | TBD | S4-01..S4-05 |

### Sprint Review Checklist
- [ ] All 7 work packages complete
- [ ] `make check` passes
- [ ] `make security` passes
- [ ] `make test` passes
- [ ] `make typecheck` passes
- [ ] No `pass`-only methods in production code

---

## Capacity Summary

| Sprint | Work Packages | Story Points | Working Days |
|--------|---------------|--------------|--------------|
| Sprint 1 | WP-01 | 6 | 10 |
| Sprint 2 | WP-02 | 9 | 10 |
| Sprint 3 | WP-03, WP-04, WP-05 | 10 | 10 |
| Sprint 4 | WP-06, WP-07 | 6 | 10 |
| **Total** | **7 packages** | **31 SP** | **40 days** |
