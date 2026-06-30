# Decision Register

> A lightweight Architecture Decision Record (ADR) log for EAIP. One row per decision; one detailed section below.
> Format inspired by Michael Nygard's ADRs, kept deliberately terse.

| ID       | Title                                        | Status     | Date       | Supersedes |
| -------- | -------------------------------------------- | ---------- | ---------- | ---------- |
| DR-0001  | License: Apache 2.0                          | Accepted   | 2026-01-15 | —          |
| DR-0002  | Tooling: ruff + black + mypy + pytest        | Accepted   | 2026-01-15 | —          |
| DR-0003  | Policy DSL — wrap OPA/Rego (provisional)     | Proposed   | 2026-01-15 | —          |
| DR-0004  | Commit Style: Conventional Commits + DCO     | Accepted   | 2026-01-15 | —          |
| DR-0005  | Branching: trunk-based with short topic branches | Accepted | 2026-01-15 | —          |
| DR-0006  | Python target: 3.11 minimum, 3.13 max        | Accepted   | 2026-01-15 | —          |
| DR-0007  | Versioning: SemVer 2.0.0, 0.x = unstable      | Accepted   | 2026-01-15 | —          |
| DR-0008  | Async-first runtime (asyncio)                | Accepted   | 2026-01-15 | —          |
| DR-0009  | Persistence: Postgres + Redis at v1          | Accepted   | 2026-01-15 | —          |
| DR-0010  | Telemetry: OpenTelemetry as the only contract| Accepted   | 2026-01-15 | —          |

Status legend: **Proposed · Accepted · Deprecated · Superseded**.

---

## DR-0001 — License: Apache 2.0

- **Context:** EAIP is meant for enterprise adoption; users need patent grants, the ability to ship modified versions, and predictable compliance.
- **Decision:** Adopt **Apache License 2.0** for the entire repository.
- **Alternatives:** MIT (no explicit patent grant), GPL-3.0 (copyleft inappropriate for an embeddable platform), proprietary (would prevent open contribution).
- **Consequences:**
  - All contributors must agree to the DCO.
  - `LICENSE` and per-file SPDX headers (where appropriate) maintained.
  - Compatible with most enterprise OSS programmes.

## DR-0002 — Tooling: ruff + black + mypy + pytest

- **Context:** Need a fast, modern, batteries-included Python developer experience.
- **Decision:** Standardise on:
  - **`ruff`** for linting & import sorting (rule set includes E, F, W, I, B, S, UP, PERF, RUF).
  - **`black`** as the canonical formatter (line length 100).
  - **`mypy --strict`** for type checking.
  - **`pytest`** (+ `pytest-cov`, `pytest-asyncio`, `hypothesis`) for tests.
- **Alternatives:** flake8 + isort + pylint (slower, more config), pyright (excellent, but mypy aligns better with our type stubs strategy at v1).
- **Consequences:** Enforced via `pre-commit` and CI. Editor configs ship in `.vscode/`.

## DR-0003 — Policy DSL: wrap OPA/Rego *(provisional)*

- **Context:** A pluggable, auditable policy engine is required, and re-inventing Rego is expensive.
- **Decision:** v1 policy engine **wraps OPA/Rego** with a typed Python facade. Final contract reviewed in EP-0007.
- **Alternatives:** Pure-Python rules engine (faster to ship, less ecosystem), Cedar (newer, less mature).
- **Consequences:** Adds a Go binary dependency for self-hosted; offset by a pure-Python evaluator for tests.
- **Status:** **Proposed** — formal acceptance during EP-0007.

## DR-0004 — Commit Style: Conventional Commits + DCO

- **Context:** Automated changelogs and release-please require a strict commit grammar; DCO replaces a heavyweight CLA.
- **Decision:**
  - Enforce **Conventional Commits 1.0.0**.
  - Require `Signed-off-by` (**DCO**) on every commit.
- **Consequences:** `pre-commit` and CI validate both. Squash-merges preserve the PR title (which is also validated).

## DR-0005 — Branching: trunk-based with short topic branches

- **Context:** Long-lived feature branches diverge, cause merge debt, and obscure progress.
- **Decision:** `main` is always releasable. Topic branches live ≤ 2 weeks. Long features hide behind feature flags.
- **Consequences:** Requires solid CI and feature-flag tooling (introduced incrementally from EP-0001B).

## DR-0006 — Python target: 3.11 minimum, 3.13 maximum

- **Context:** Need `TaskGroup`, `ExceptionGroup`, performance improvements, and stable type generics.
- **Decision:** Support **3.11, 3.12, 3.13**. Drop a version 6 months after its EOL.
- **Consequences:** May use `typing.Self`, `tomllib`, `Exception groups`, and PEP 695 generics in 3.12+ paths (guarded if needed).

## DR-0007 — Versioning: SemVer 2.0.0

- **Context:** Enterprise users require predictable upgrade rules.
- **Decision:** Follow [SemVer 2.0.0](https://semver.org/). While `0.x`, minor versions may introduce breaking changes; patch versions never do.
- **Consequences:** Full policy in [`VERSIONING.md`](VERSIONING.md). Release-please used for version automation.

## DR-0008 — Async-first runtime (asyncio)

- **Context:** Most agent work is I/O-bound (LLM calls, tool calls). Sync Python would serialise this needlessly.
- **Decision:** The runtime is **`asyncio`-native**. CPU-bound work uses bounded executors.
- **Alternatives:** Trio (smaller ecosystem), threads (GIL contention).
- **Consequences:** All public contracts are `async`. Tests use `pytest-asyncio`.

## DR-0009 — Persistence: Postgres + Redis at v1

- **Context:** Need a durable, ACID store and a fast, ephemeral one.
- **Decision:** **PostgreSQL** for durable state (runs, audit, config). **Redis** for ephemeral state (queues, STM, locks).
- **Alternatives:** Single store (cognitive simplicity, perf tradeoffs); NoSQL durable (loses transactions).
- **Consequences:** Two infra dependencies; operators must run/manage both. Both have managed-cloud equivalents.

## DR-0010 — Telemetry: OpenTelemetry as the only contract

- **Context:** Vendor-neutral, broadly supported, and the de-facto industry standard.
- **Decision:** Emit traces, metrics, and logs through **OpenTelemetry**. No vendor-specific SDKs in the core.
- **Consequences:** Operators choose the backend (Tempo, Honeycomb, Datadog, …) via OTel exporters.

---

## Adding a New Decision

1. Open a discussion or issue describing the choice and trade-offs.
2. On consensus, append a row to the table and a section below.
3. Use the next sequential ID. **Never** mutate or delete prior entries; supersede instead.
