# EAIP Alpha Roadmap

> **Horizon:** 8 weeks (2026-07-14 → 2026-09-05)
> **Objective:** Resolve all P0 and P1 findings from the Architecture Audit, achieve Alpha release readiness.
> **Owner:** Subham Panigrahi (@subham1902)
> **Last updated:** 2026-07-11

---

## Phase Overview

```
Week 1-2     Week 3-4     Week 5-6     Week 7-8
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Alpha-1  │ │  Alpha-2  │ │  Alpha-3  │ │  Alpha-4  │
│ Security  │ │ Event Bus │ │ Error     │ │ Stubs     │
│ Hardening │ │ Fix       │ │ Handling  │ │ + Polish  │
│ WP-01     │ │ WP-02     │ │ WP-03,05  │ │ WP-06,07  │
│           │ │           │ │ WP-04     │ │           │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
                                    │
                              Alpha Release
                              Candidate
```

---

## Phase Alpha-1: Security Hardening (Week 1-2, Jul 14-25)

**Work Package:** WP-01 (Security Hardening)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | **JWT secret fix** — replace hardcoded default with `SecretProviderPort` | `auth/tokens.py` updated, no hardcoded secret |
| 2-3 | **Data pipeline exec fix** — replace `exec()` with AST-based restricted evaluation or declarative transform DSL | `datapipeline/steps.py` no longer uses `exec()` |
| 3-4 | **Integration transform exec fix** — same approach | `integration/transform.py` no longer uses `exec()` |
| 4-5 | **Shell injection fix** — replace `create_subprocess_shell` with `create_subprocess_exec` | `automation/executor.py` uses safe subprocess API |
| 5 | **Security regression tests** — verify each fix with bandit + unit tests | All security checks passing |

**Exit Criteria:**
- Bandit scan: zero high-severity findings
- `make security` passes
- No new `mypy --strict` errors
- All existing tests pass

---

## Phase Alpha-2: Event Bus Reliability (Week 3-4, Jul 28 - Aug 8)

**Work Package:** WP-02 (Event Bus Reliability)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | **Auth events** — wire `tokens.py` and `auth_providers.py` `_emit()` to `EventBus` | Auth events published to EventBus |
| 2-3 | **Orphaned events (Part 1)** — fix `apiext/caching.py`, `gateway/router.py`, `sandbox/manager.py` | Events published via `EventBus` |
| 3-4 | **Orphaned events (Part 2)** — fix `bluegreen/manager.py`, `observability/slo.py`, `firewall/manager.py` | Events published via `EventBus` |
| 4-5 | **Orphaned events (Part 3)** — fix `eventret/manager.py`, `xbridge/bridge.py` | Events published via `EventBus` |
| 5-6 | **Unawaited coroutine** — fix `collaboration/coordinator.py:_publish()` to await | Collaboration events delivered |
| 6-7 | **Consolidate dispatch patterns** — migrate custom `_emit()`/`_event_callback` patterns to `EventBus` | Single event dispatch pattern across platform |
| 7-8 | **Integration tests** — end-to-end event delivery verification | Auth event end-to-end test passes |

**Exit Criteria:**
- Zero orphaned event construction without publishing
- `collaboration` events are delivered
- Auth events appear in audit trail
- Integration test verifies end-to-end event flow

---

## Phase Alpha-3: Error Handling & Async Correctness (Week 5-6, Aug 11-22)

**Work Packages:** WP-03 (Error Handling), WP-04 (Async Correctness), WP-05 (Time & Data)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-3 | **Bare except audit** — eliminate all 71+ `except Exception: pass` patterns | Zero silent error swallowing |
| 3-4 | **ensure_future → create_task** — fix `audit/store.py` | Proper task tracking |
| 4 | **Error codes** — assign distinct codes to event errors | Diagnostic specificity |
| 4-5 | **Async locks** — replace `threading.Lock()` with `asyncio.Lock()` | Event loop safety |
| 5-6 | **SDK async fix** — convert sync SDK methods or use consistent async bridging | No deadlock risk |
| 6-7 | **Time hygiene** — replace all `datetime.now()` with `utc_now()` | Timezone-safe code |
| 7-8 | **Token eviction** — add TTL-based garbage collection | Memory leak fixed |

**Exit Criteria:**
- `grep -r "except Exception: pass" src/eaip/` returns zero results
- `make typecheck` passes
- Token eviction test passes

---

## Phase Alpha-4: Stubs & Polish (Week 7-8, Aug 25 - Sep 5)

**Work Packages:** WP-06 (Stub Completion), WP-07 (Code Quality)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | **S3ArchiveStore** — implement with `boto3` or replace with clear error message | No dead code |
| 2-3 | **Deployment strategies** — implement rolling deploy via subprocess | At least one working strategy |
| 3-4 | **CLI shell** — wire `run_forever()` to actually execute commands | Interactive CLI works |
| 4-5 | **Code quality fixes** — private attribute access, import hygiene | Ruff `PLC0415` passes |
| 5-6 | **Alpha release candidate prep** | All gates passing |

**Exit Criteria:**
- All 7 work packages complete
- `make check` passes
- `make security` passes
- `make test` passes with no regressions

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `exec()` replacement breaks data pipeline functionality | High | Medium | Add declarative transform tests before replacing; keep both in parallel during migration |
| Event bus fix reveals latent race conditions | Medium | Low | Add concurrent delivery tests; use EventDispatcher retry strategy |
| `threading.Lock()` → `asyncio.Lock()` introduces new deadlocks | Medium | Low | Review each replacement for correct lock ordering |
| Token eviction changes behavior for long-lived sessions | Medium | Medium | Add configurable-TTL with sensible defaults; document migration |
