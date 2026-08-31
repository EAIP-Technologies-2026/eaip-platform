# EAIP Alpha Backlog

> **Purpose:** Organize all verified architecture audit findings into Engineering Work Packages for Alpha stabilization.
> **Source:** `MASTER_AUDIT.md` — 33 verified findings consolidated into 7 work packages.
> **Owner:** Subham Panigrahi (@subham1902)
> **Last updated:** 2026-07-11

---

## Work Package Index

| WP | Title | Findings | Priority | Est. Complexity | Dependencies |
|----|-------|----------|----------|-----------------|--------------|
| WP-01 | Security Hardening | 4 Critical | P0 — Alpha Blocker | M (3-5 days) | WP-03 (error handling) |
| WP-02 | Event Bus Reliability | 11 High + 1 Medium | P0 — Alpha Blocker | L (5-8 days) | WP-03 |
| WP-03 | Error Handling Discipline | 2 High + 1 Medium | P1 — Required | M (3-5 days) | None |
| WP-04 | Async Correctness | 4 Medium | P1 — Required | S (2-3 days) | None |
| WP-05 | Time & Data Hygiene | 1 High + 5 Medium | P1 — Required | M (3-5 days) | WP-04 |
| WP-06 | Stub Implementation Completion | 3 High | P2 — Nice to Have | M (3-5 days) | WP-02 |
| WP-07 | Code Quality & Consistency | 3 Low | P2 — Nice to Have | S (1-2 days) | None |

---

## WP-01: Security Hardening

**Objective:** Eliminate all critical security vulnerabilities that could lead to account takeover or remote code execution.

**Included Findings:**

| ID | Finding | File | Line | Risk |
|----|---------|------|------|------|
| C-001 | Hard-coded JWT default secret | `auth/tokens.py` | 83 | Account takeover |
| C-002 | Unrestricted `exec()` in data pipeline | `datapipeline/steps.py` | 222 | RCE |
| C-004 | `exec()` in integration transform | `integration/transform.py` | 121 | RCE |
| C-005 | Shell injection in automation executor | `automation/executor.py` | 106-109 | RCE |

**Dependencies:** WP-03 (error handling — bare except clauses around security-sensitive code must be addressed first)

**Acceptance Criteria:**
- JWT secret is no longer a hard-coded default — uses `SecretProviderPort` or environment variable
- `datapipeline/steps.py:exec()` is replaced with AST-based restricted evaluation or removed
- `integration/transform.py:exec()` is replaced with a safe transform DSL
- `automation/executor.py:create_subprocess_shell` is replaced with `create_subprocess_exec` with explicit argument array

**Definition of Done:**
- All four fixes merged to main
- Each fix has a unit test covering the attack vector
- No new `mypy --strict` errors
- No new `ruff` errors
- Bandit scan passes with zero new findings

---

## WP-02: Event Bus Reliability

**Objective:** Ensure all domain events are actually delivered to subscribers. Currently the event-driven architecture is partially non-functional because events are silently dropped at three different points in the pipeline.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| H-001 | Auth events no-op (tokens) | `auth/tokens.py` | 256-257 |
| H-002 | Auth events no-op (auth_providers) | `auth/auth_providers.py` | 223-224 |
| H-004 | Orphaned events in caching | `apiext/caching.py` | 44,49,65,129 |
| H-005 | Orphaned events in router | `gateway/router.py` | 52,69,129-135 |
| H-006 | Orphaned events in sandbox | `sandbox/manager.py` | 41-45,62,74-81,103-107,128-132 |
| H-007 | Orphaned events in bluegreen | `bluegreen/manager.py` | 83-88,111-116,126-131,137-141 |
| H-008 | Orphaned events in SLO | `observability/slo.py` | 82-97 |
| H-009 | Orphaned events in firewall | `firewall/manager.py` | 34-39,59-62,70-73 |
| H-010 | Orphaned events in eventret | `eventret/manager.py` | 38-43 |
| H-011 | Orphaned events in xbridge | `xbridge/bridge.py` | 42-47,68-71,84-88 |
| H-012 | Unawaited coroutine in collaboration dispatch | `collaboration/coordinator.py` | 530-535 |
| M-011 | Event dispatching inconsistency (3 patterns) | Multiple | Various |

**Dependencies:** WP-03 (error handling — event dispatch must not silently swallow errors)

**Acceptance Criteria:**
- `TokenService._emit()` and `AuthenticationService._emit()` publish to `EventBus`
- All 8 packages with orphaned events publish to `EventBus` or `EventDispatcher`
- `collaboration/coordinator.py:_publish()` awaits the coroutine
- Custom `_emit()`/`_event_callback` patterns are migrated to `EventBus`
- Integration test verifies end-to-end event delivery for auth events

**Definition of Done:**
- All event-producing services properly publish to EventBus
- `pytest` passes with no regressions
- A new integration test verifies auth event end-to-end flow
- Documentation updated in affected READMEs

---

## WP-03: Error Handling Discipline

**Objective:** Eliminate silent error swallowing. Ensure every exception is at minimum logged with structured context.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| H-003 | 71+ bare `except Exception: pass` | 40+ files | Various |
| H-017 | `asyncio.ensure_future()` fire-and-forget | `audit/store.py` | 104-113,127-136 |
| M-008 | Error codes all `UNKNOWN` | `events/errors.py` | 11,17,23,29 |

**Dependencies:** None

**Acceptance Criteria:**
- Every `except Exception:` block either logs the error, re-raises a typed exception, or both
- `asyncio.ensure_future()` is replaced with `asyncio.create_task()` with tracked task reference
- `events/errors.py` exception classes use distinct `ErrorCode` values

**Definition of Done:**
- Zero `except Exception: pass` patterns remain in `src/eaip/`
- Audit of all `except Exception:` blocks completed with structured logging
- New `ErrorCode` values assigned to event error types
- Ruff `ERA001` (eradicate dead code) enabled and passing

---

## WP-04: Async Correctness

**Objective:** Fix all async/threading violations that can cause event loop blocking, deadlocks, or undefined behavior.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| M-001 | `threading.Lock()` in async code | `gateway/rate_limiter.py` | 32 |
| M-002 | `threading.Lock()` in schema registry | `schema/registry.py` | (internal) |
| M-003 | `anyio.from_thread.run()` anti-pattern | `sdk/clients.py` | 57-60,77-80 |
| M-004 | `anyio.from_thread.run()` anti-pattern | `sdk/manager.py` | 77-80,167-171,210-221 |

**Dependencies:** None

**Acceptance Criteria:**
- `gateway/rate_limiter.py` uses `asyncio.Lock()` instead of `threading.Lock()`
- `schema/registry.py` uses `asyncio.Lock()` instead of `threading.Lock()`
- `sdk/clients.py` and `sdk/manager.py` synchronous methods are converted to `async def` or use `asyncio.run()` consistently

**Definition of Done:**
- Zero `threading.Lock` instances in async code paths
- All tests pass
- No new mypy or ruff errors

---

## WP-05: Time & Data Hygiene

**Objective:** Standardize time handling, fix memory leaks, eliminate type shadowing, and remove dead code.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| H-013 | In-memory token storage unbounded growth | `auth/tokens.py` | 87-88 |
| M-005 | `datetime.now()` without UTC | `collaboration/coordinator.py` | 109 |
| M-006 | `datetime.now()` without UTC | `collaboration/delegation.py` | 49 |
| M-007 | Type shadowing `Bytes` | `shared/types.py` | 23 |
| M-009 | Dead code in compliance scoring | `compliance/framework.py` | 108 |
| M-010 | Private attribute access across classes | `events/dispatcher.py` | 150 |

**Dependencies:** WP-04 (async correctness — token cleanup may need async expiry sweeper)

**Acceptance Criteria:**
- Token storage implements TTL-based eviction or bounded capacity
- All `datetime.now()` calls are replaced with `utc_now()` from `eaip.shared.time` or explicit `datetime.now(UTC)`
- `shared/types.py` `Bytes` alias renamed or removed
- Compliance scoring dead code removed
- `events/dispatcher.py` accesses `EventBus` via public API

**Definition of Done:**
- Token garbage collection verified in unit test
- Zero naive `datetime.now()` calls in production code
- Linting catches `datetime.now()` without UTC (enable ruff `DTZ` rules)

---

## WP-06: Stub Implementation Completion

**Objective:** Complete or remove stub implementations that crash at runtime or provide no functionality.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| H-014 | `S3ArchiveStore` fully unimplemented | `archive/store.py` | 59-81 |
| H-015 | Deployment strategies are empty stubs | `deploy/deployer.py` | 184-194 |
| H-016 | CLI `run_forever()` yields no-op infinitely | `cli/shell.py` | 73-78 |

**Dependencies:** WP-02 (event bus — some stubs need event publishing)

**Acceptance Criteria:**
- `S3ArchiveStore` is either fully implemented with `boto3` or removed with a clear error message
- `deploy/deployer.py` deployment strategies either execute real deployment logic or raise a clear `NotImplementedError` with documentation
- `cli/shell.py:run_forever()` reads input and dispatches to `execute()`

**Definition of Done:**
- No `pass`-only methods remain in production code
- No `NotImplementedError` without documentation and tracking issue
- CLI shell can execute commands in interactive mode

---

## WP-07: Code Quality & Consistency

**Objective:** Fix minor encapsulation violations and import hygiene issues.

**Included Findings:**

| ID | Finding | File | Line |
|----|---------|------|------|
| L-001 | Private attribute access (`_regulation_controls`) | `compliance/framework.py` | 95-96 |
| L-002 | Module-level import inside method | `automation/engine.py` | 316 |
| L-003 | Module-level import inside method | `schema/registry.py` | 52 |

**Dependencies:** None

**Acceptance Criteria:**
- `compliance/framework.py` accesses `RegulationMapper` controls through public method
- All `import` statements are at module top level

**Definition of Done:**
- Ruff `PLC0415` (import-outside-top-level) enabled and passing
- No regressions
