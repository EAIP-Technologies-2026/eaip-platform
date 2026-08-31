# Definition of Done — EAIP Alpha

> **Purpose:** Standardized acceptance criteria that every Alpha work item must satisfy before it can be marked complete.
> **Applies to:** All work packages (WP-01 through WP-07) in the Alpha stabilization backlog.
> **Last updated:** 2026-07-11

---

## Required Gates

Every Alpha work item must pass ALL of the following gates:

### Gate 1: Code Quality

| Criterion | Validation | Tool |
|-----------|------------|------|
| No `mypy --strict` errors | `mypy --strict src/` exits 0 | mypy 2.1+ |
| No `ruff` lint errors | `ruff check src/` exits 0 | ruff 0.15+ |
| No `ruff` format drift | `ruff format --check src/` exits 0 | ruff 0.15+ |
| No `black` format drift | `black --check src/` exits 0 | black 26.5+ |
| No `print()` statements in production code | Manual review + grep | — |
| No `TODO`, `FIXME`, `HACK`, `XXX` without tracking issue | `todo-tree` scan | — |

### Gate 2: Testing

| Criterion | Validation | Tool |
|-----------|------------|------|
| All existing tests pass | `pytest tests/` exits 0 | pytest |
| Coverage does not decrease | Compare against baseline | pytest-cov |
| New code has ≥85% line coverage | `pytest --cov=src/eaip/<module>` | pytest-cov |
| New functionality has at least one integration test | Test file in `tests/integration/` | pytest |
| Security fixes have regression tests | Test file verified by reviewer | pytest |

### Gate 3: Security

| Criterion | Validation | Tool |
|-----------|------------|------|
| No new bandit findings | `bandit -c pyproject.toml -r src/` exits 0 | bandit |
| No `exec()` / `eval()` in new or modified code | Manual review | — |
| No `create_subprocess_shell` in new or modified code | `grep` | — |
| No hard-coded secrets or credentials | `detect-secrets` scan | detect-secrets |
| No `except Exception: pass` without justification | Manual review | — |

### Gate 4: Architecture

| Criterion | Validation |
|-----------|------------|
| No circular imports introduced | `pip install -e . && python -c "import eaip"` succeeds |
| No imports from higher-layer packages | Reviewer verification |
| New events use `EventBus.publish()` — not orphaned construction | Code review |
| New exceptions use distinct `ErrorCode` values | Code review |
| No `TYPE_CHECKING` imports that could be resolved at runtime | Reviewer verification |

### Gate 5: Documentation

| Criterion | Validation |
|-----------|------------|
| Public API has Google-style docstring | `ruff check --select D` |
| `README.md` updated if package interface changed | Reviewer verification |
| `CHANGELOG.md` entry added | Manual |
| If behavior changed, `DECISION_REGISTER.md` updated | Manual |

---

## Per-Work-Package DoD

### WP-01: Security Hardening
All of the above, plus:
- [ ] Bandit scan: zero medium+ findings
- [ ] JWT secret is not hard-coded anywhere in `src/eaip/auth/`
- [ ] No `exec()` remains in `datapipeline/steps.py` or `integration/transform.py`
- [ ] No `create_subprocess_shell` remains in `automation/executor.py`

### WP-02: Event Bus Reliability
All of the above, plus:
- [ ] `TokenService._emit()` publishes to `EventBus`
- [ ] `AuthenticationService._emit()` publishes to `EventBus`
- [ ] Zero orphaned event constructions remain (verify by grep for pattern `EventType(...)` without `.publish` or assignment to bus variable)
- [ ] All three event dispatch patterns consolidated to `EventBus`
- [ ] End-to-end integration test verifies auth event delivery

### WP-03: Error Handling Discipline
All of the above, plus:
- [ ] Zero `except Exception: pass` patterns in `src/eaip/`
- [ ] `asyncio.ensure_future()` replaced with `asyncio.create_task()` in `audit/store.py`
- [ ] `events/errors.py` exception classes have distinct `ErrorCode` values

### WP-04: Async Correctness
All of the above, plus:
- [ ] Zero `threading.Lock` instances in async code paths
- [ ] `anyio.from_thread.run()` replaced in `sdk/`

### WP-06: Stub Implementation Completion
All of the above, plus:
- [ ] No `pass`-only methods in production code
- [ ] No `raise NotImplementedError` without documentation and tracking issue
- [ ] CLI `run_forever()` reads input and dispatches to `execute()`
