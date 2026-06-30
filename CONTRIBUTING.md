# Contributing to EAIP

First, thank you for considering a contribution. EAIP is built on the work of many people; we aim to make participation rewarding, low-friction, and respectful of everyone's time.

This document describes **how to contribute** to the Enterprise Autonomous Intelligence Platform. It applies to code, documentation, design, tests, and infrastructure.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Branching Model](#branching-model)
- [Commit Messages](#commit-messages)
- [Sign-Off (DCO)](#sign-off-dco)
- [Pull Requests](#pull-requests)
- [Code Review](#code-review)
- [Coding Standards](#coding-standards)
- [Testing Standards](#testing-standards)
- [Documentation Standards](#documentation-standards)
- [Engineering Packages (EPs)](#engineering-packages-eps)
- [Reporting Bugs & Requesting Features](#reporting-bugs--requesting-features)
- [Security Issues](#security-issues)
- [Governance](#governance)

---

## Code of Conduct

This project and everyone participating in it is governed by the [EAIP Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Report unacceptable behaviour to **conduct@eaip.dev**.

## Ways to Contribute

- **Code** — bug fixes, features, refactors, performance.
- **Documentation** — guides, tutorials, API reference, examples.
- **Tests** — unit, integration, property-based, fuzz, e2e.
- **Triage** — reproducing bugs, labelling issues, helping new contributors.
- **Design** — UX, diagrams, accessibility audits.
- **Operations** — CI, release tooling, observability dashboards.

If you are not sure where to start, look for issues labelled [`good first issue`](https://github.com/subham1902/eaip-platform/labels/good%20first%20issue) or [`help wanted`](https://github.com/subham1902/eaip-platform/labels/help%20wanted).

## Getting Started

### Prerequisites

- **Python** 3.11, 3.12, or 3.13
- **Git** 2.35+
- **GNU Make** 4+
- **Docker** 24+ *(only required for integration/e2e tests; arrives in EP-0002)*

### Bootstrap

```bash
git clone https://github.com/subham1902/eaip-platform.git
cd eaip-platform
make bootstrap        # creates .venv/, installs dev deps, installs pre-commit hooks
```

Verify your environment:

```bash
make check            # runs all quality gates locally
```

## Development Workflow

1. **Find or open an issue.** Discuss design *before* writing significant code. PRs that arrive without an issue for non-trivial changes may be asked to back up.
2. **Fork** the repository and create a topic branch (see [Branching Model](#branching-model)).
3. **Write code + tests + docs together.** All three are first-class deliverables.
4. **Run `make check`** locally until green.
5. **Open a Pull Request** against `main` using the PR template.
6. **Iterate** with reviewers. Keep the PR small and focused.
7. **Squash-merge** when approved (maintainers handle this).

## Branching Model

- `main` — always releasable. Protected. Merges via PR only.
- `release/x.y` — maintenance branches for shipped minor versions.
- Topic branches — `<type>/<short-kebab-summary>` (e.g., `feat/policy-engine`, `fix/token-budget-overflow`, `docs/security-policy`).

We do **not** use long-lived feature branches. If your work spans multiple PRs, gate it behind a feature flag.

## Commit Messages

We follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

```
<type>(<scope>)!: <subject>

<body>

<footer>
```

- **type** ∈ `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `revert`.
- `!` denotes a **breaking change** (also requires a `BREAKING CHANGE:` footer).
- **scope** is a short package or area name (`runtime`, `policy`, `cli`, `docs`, etc.).
- **subject** is imperative mood, ≤ 72 chars, no trailing period.
- **body** explains *what* and *why*, not *how*.
- **footer** carries metadata: `Refs: #123`, `Closes: #456`, `BREAKING CHANGE: …`, `Signed-off-by: …`.

Example:

```
feat(runtime): add token-budget enforcement to orchestrator

Introduces per-request and per-tenant token budgets enforced before each
LLM call. Budgets are configurable via PolicySpec and emit OTel events
on exhaustion.

Closes: #142
Signed-off-by: Jane Doe <jane@example.com>
```

## Sign-Off (DCO)

Every commit must carry a `Signed-off-by` trailer asserting the [Developer Certificate of Origin](https://developercertificate.org/):

```bash
git commit -s -m "feat(cli): add `eaip agents list` command"
```

The DCO check is enforced in CI. Unsigned commits will block the merge.

## Pull Requests

- One logical change per PR. If you find yourself writing "and also" in the description, split it.
- Keep diffs **< 400 lines** of non-generated code where possible.
- Fill in the PR template completely — checklist items are not decoration.
- Link the issue(s) you close: `Closes #NNN`.
- Mark draft PRs as **Draft** until ready for review.
- Rebase (don't merge) `main` into your branch to stay current.
- CI must be **green** before requesting review.

## Code Review

- Reviews are mandatory: **at least one** maintainer approval required; **two** for changes to `src/eaip/runtime/`, `src/eaip/policy/`, or anything under `/.github/workflows/`.
- Reviewers respond within **2 business days**. If you need faster turnaround, ping in the issue.
- Authors are expected to respond to feedback within **5 business days**, else the PR is closed as stale (re-open anytime).
- Be kind, be concrete, suggest code where useful, distinguish *blocking* from *nit*.

## Coding Standards

- **Formatter:** `black` (line length 100) + `ruff format`.
- **Linter:** `ruff` with the configured rule set (see `pyproject.toml`).
- **Types:** `mypy --strict`. Public APIs are fully typed; `Any` requires justification.
- **Imports:** sorted by `ruff` (isort rules). Absolute imports only.
- **Logging:** use the project's `structlog` configuration; **never** print.
- **Errors:** raise the most specific exception; never `except:` or `except Exception:` without re-raising or logging with context.
- **Public APIs:** documented with Google-style docstrings + executable examples where reasonable.
- **Side effects** at import time are forbidden.

## Testing Standards

- Tests live under `tests/` mirroring the `src/` layout.
- Use **pytest** + **pytest-cov** + **hypothesis** (property-based) where appropriate.
- Each new feature ships with tests. Each bug fix ships with a regression test.
- Coverage gate: **85% lines / 80% branches** (enforced in CI from EP-0002).
- Tests must be **deterministic**. No real network, real LLMs, or wall-clock dependence.

## Documentation Standards

- Update `README.md`, `ARCHITECTURE.md`, and any relevant doc when behaviour or contracts change.
- Add an entry to `CHANGELOG.md` under `## [Unreleased]` using the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) categories.
- New architectural decisions get an entry in `DECISION_REGISTER.md` (lightweight ADR).
- New risks or debt get logged in `RISK_REGISTER.md` / `TECH_DEBT.md` with an owner.

## Engineering Packages (EPs)

Significant work is organised into **Engineering Packages**. Each EP has:

- A unique ID (`EP-NNNNX` where `X` is the iteration letter).
- A scope, deliverables, acceptance criteria, and owner.
- Entries in [`ENGINEERING_TRACKER.md`](ENGINEERING_TRACKER.md).

If your contribution belongs to an EP, reference it in commits and PR descriptions (e.g., `Refs: EP-0002`).

## Reporting Bugs & Requesting Features

Use the **issue templates** under `.github/ISSUE_TEMPLATE/`:

- 🐛 **Bug report** — reproducible defect.
- ✨ **Feature request** — new capability or improvement.
- 📚 **Documentation** — corrections, gaps, examples.

Always search existing issues first.

## Security Issues

**Do not file public issues for security vulnerabilities.** Follow the coordinated disclosure process in [`SECURITY.md`](SECURITY.md).

## Governance

- **BDFL / Lead Maintainer:** Subham Panigrahi ([@subham1902](https://github.com/subham1902)).
- **Maintainers:** listed in [`.github/CODEOWNERS`](.github/CODEOWNERS).
- **Decisions:** consensus-seeking; lead maintainer breaks ties. Significant decisions are recorded in [`DECISION_REGISTER.md`](DECISION_REGISTER.md).

Thanks again — happy hacking! 🚀
