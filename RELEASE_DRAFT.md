# RELEASE DRAFT — EAIP Alpha Foundation v1.0

> Draft for the GitHub release of `eaip-platform`. Adjust before publishing.

## Metadata

| Field | Value |
|---|---|
| Release | `alpha-foundation-v1.0` |
| Tag | `alpha-foundation-v1.0` |
| Branch | `alpha-integration` |
| Commit | `fcb0941` `feat(runtime): release Alpha Foundation v1.0` |
| Status | Published (branch + tag pushed to `origin`) |

## Summary

Alpha Foundation baseline for the EAIP runtime platform:

- **Database module** (`src/eaip/db/`) with settings and `DatabaseConnection`, wired into startup via the DI container
- **Observability manager** (`src/eaip/observability/manager.py`) and `src/eaip/ports/observability.py` port contract
- **Integrations namespace** (`src/eaip/integrations/`) for external adapters (Sentry, BetterStack)
- **Health contract** standardized on `healthy / skipped / degraded / unhealthy`; `/ready` and `/live` return `"healthy"` when green
- **Startup hardening**: fails fast when `EAIP_AUTH_SECRET` is missing (no dev default)
- **Seed tooling** (`scripts/seed_alpha_demo.py`) plus 6 new unit test modules

## Verification

| Gate | Result |
|---|---|
| pytest (suite) | 9282 passed, 10 skipped, **4 failed** |
| ruff check | FAIL — 6962 errors (211 fixable) |
| ruff format --check | FAIL — 77 files unformatted |
| mypy | FAIL — 1294 errors in 303 files |
| pre-commit run --all-files | FAIL — markdownlint (MD022/MD032/MD040) |

## Known issues (do not block publish)

- **Test contract drift:** `tests/test_stabilization.py` still asserts `"ready"`/`"alive"` while endpoints now return `"healthy"` — the 4 failures are the old contract; update the tests to the new status model.
- Pre-existing lint/format/type debt (counts above) predates this release and is tracked in `TECH_DEBT.md`.

## Checklist

- [x] Baseline committed on `alpha-integration` (`fcb0941`)
- [x] Branch pushed to `origin`
- [x] Tag `alpha-foundation-v1.0` created and pushed
- [ ] Publish release notes on GitHub (copy from this draft)
