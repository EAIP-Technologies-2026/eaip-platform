# Technical Debt Register

> **Purpose:** Track conscious shortcuts, deferred work, and known suboptimal choices so they don't quietly accrete.
> **Convention:** Every entry has an **owner**, a **trigger** (when it should be revisited), and a **cost-of-delay** estimate.
> **Last updated:** 2026-01-15

---

## Scoring

- **Severity:** `low` (cosmetic), `medium` (slows development), `high` (risks reliability/security), `critical` (blocks features or carries risk).
- **Effort:** `S` (≤ 1 day), `M` (≤ 1 week), `L` (≤ 1 month), `XL` (> 1 month).
- **Cost of Delay (CoD):** qualitative — how much pain compounds if untouched another quarter.

## Open Debt

| ID      | Title                                              | Severity | Effort | CoD      | Owner       | Trigger                   |
| ------- | -------------------------------------------------- | -------- | ------ | -------- | ----------- | ------------------------- |
| TD-0001 | No coverage gate yet                               | medium   | S      | medium   | @subham1902 | When EP-0002 lands tests. |
| TD-0002 | No published docs site                             | medium   | M      | medium   | TBD         | Before `0.1.0`.           |
| TD-0003 | Issue/PR templates lack auto-labelling             | low      | S      | low      | @subham1902 | When triage volume > 5/wk.|
| TD-0004 | No SBOM/cosign on releases                         | high     | M      | high     | TBD         | EP-0013.                  |
| TD-0005 | CHANGELOG curated manually                         | medium   | S      | medium   | @subham1902 | EP-0001B (release-please).|
| TD-0006 | No threat model document                           | high     | L      | high     | TBD         | EP-0017.                  |
| TD-0007 | Single maintainer (`@subham1902`) → bus factor = 1 | critical | XL     | critical | @subham1902 | After 1st external contributor. |
| TD-0008 | No performance baselines or SLOs                   | medium   | L      | medium   | TBD         | EP-0018.                  |
| TD-0009 | `mypy --strict` not yet applied to a real package  | low      | S      | low      | @subham1902 | EP-0002.                  |
| TD-0010 | Conventional-commit enforcement is pre-commit only | low      | S      | low      | @subham1902 | When external PRs arrive. |

## Resolved Debt

| ID | Title | Resolved In | Notes |
| -- | ----- | ----------- | ----- |
| —  | —     | —           | —     |

---

## Detail

### TD-0001 — No coverage gate yet

- **Why it exists:** EP-0001A does not yet ship runtime code; gating coverage on an empty repo creates noise.
- **Resolution plan:** When EP-0002 introduces `src/eaip/runtime/`, set CI to fail below **85% lines / 80% branches**, with `--cov-fail-under` enforced in `pyproject.toml`.

### TD-0002 — No published docs site

- **Why it exists:** Foundation prioritised governance files; long-form docs need tooling (MkDocs Material or Sphinx) and CI.
- **Resolution plan:** Stand up MkDocs Material in `docs/` with a `gh-pages` deploy workflow; target before `0.1.0`.

### TD-0003 — Issue/PR templates lack auto-labelling

- **Resolution plan:** Add `actions/labeler` config plus path-based and template-based label rules.

### TD-0004 — No SBOM/cosign on releases

- **Risk:** Supply-chain attestation expected by enterprise buyers.
- **Resolution plan:** During EP-0013 — generate SPDX & CycloneDX, sign release assets with cosign keyless signing, publish provenance via SLSA L3 workflow.

### TD-0005 — CHANGELOG curated manually

- **Resolution plan:** Adopt `release-please` (or `git-cliff`) in EP-0001B to generate `CHANGELOG.md` from Conventional Commits.

### TD-0006 — No threat model document

- **Resolution plan:** EP-0017 produces a STRIDE-based threat model alongside an external pen-test.

### TD-0007 — Single maintainer → bus factor = 1

- **Risk:** Project halts if the sole maintainer is unavailable.
- **Resolution plan:** Recruit 2 additional maintainers from the first wave of external contributors; codify in CODEOWNERS and `CONTRIBUTING.md` governance section.

### TD-0008 — No performance baselines or SLOs

- **Resolution plan:** EP-0018 establishes p50/p95/p99 latency, throughput, and error-rate SLOs with synthetic and load-test harnesses.

### TD-0009 — `mypy --strict` not yet applied to a real package

- **Resolution plan:** Wire up `mypy` against `src/eaip/` in EP-0002; fix any issues immediately.

### TD-0010 — Conventional-commit enforcement is pre-commit only

- **Risk:** Contributors who skip hooks (`-n`) can land non-conforming commits.
- **Resolution plan:** Add server-side validation in CI (PR title + commitlint over the squash range).

---

## Adding a New Debt Entry

1. Append a row to **Open Debt** and a section below.
2. Set an explicit **trigger** — debt without a trigger becomes debt forever.
3. Reference any related EPs, decisions, or risks.
4. When resolved, move the row to **Resolved Debt**, do **not** delete it.
