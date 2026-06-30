# Versioning Policy

EAIP follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). This document clarifies what that means *for this project* — what counts as a breaking change, what is considered public API, how we handle pre-1.0 releases, and how deprecations work.

---

## TL;DR

- **`MAJOR.MINOR.PATCH`** — bump `MAJOR` on breaking changes, `MINOR` on backwards-compatible features, `PATCH` on backwards-compatible fixes.
- **Pre-1.0 (`0.x.y`):** breaking changes are allowed in **minor** versions; **patch** versions never break.
- **Deprecations** carry one full minor cycle's notice (post-1.0) before removal.
- **Security fixes** may ship in any version line at any time.

## What is Public API?

The following are **public** and subject to SemVer:

- Anything importable from a top-level package without leading underscores (e.g., `from eaip import …`).
- The CLI surface (`eaip <command> …`), its flags, exit codes, and stdout contracts.
- HTTP/gRPC endpoints documented under `docs/api/` (once published).
- On-disk config schemas (`pyproject.toml`-like or YAML) documented under `docs/config/`.
- Persistent data formats (database schemas, file formats) — covered by **migration guarantees**, not strict SemVer.
- Telemetry semantic conventions documented under `docs/telemetry/`.

The following are **not** public API:

- Anything in a module whose name begins with `_`.
- Anything documented as `experimental`, `preview`, or `internal`.
- Test utilities under `tests/`.
- Generated artifacts (e.g., protobuf stubs) consumed only internally.
- Exact log message wording (semantic event names *are* stable).

## Version Increment Rules

| Change                                                       | Bump   |
| ------------------------------------------------------------ | ------ |
| Removing a public symbol                                     | MAJOR  |
| Removing or renaming a CLI flag / subcommand                 | MAJOR  |
| Changing a public function signature in an incompatible way  | MAJOR  |
| Removing a config key                                        | MAJOR  |
| Tightening the type of a public field                        | MAJOR  |
| Changing default behaviour in a way users would notice       | MAJOR  |
| Adding a new public symbol / endpoint / config key           | MINOR  |
| Adding an optional parameter with a safe default             | MINOR  |
| New CLI subcommand / flag                                    | MINOR  |
| Performance improvement with no behavioural change           | PATCH  |
| Bug fix that restores documented behaviour                   | PATCH  |
| Documentation-only change                                    | PATCH  |
| Internal refactor with no public-surface change              | PATCH  |
| Security fix that *also* requires breaking the public API    | MAJOR + advisory |

## Pre-1.0 Special Rules

While we are on `0.x.y`:

- **Minor bumps may break.** Each `0.x` minor release may break compatibility; the `CHANGELOG.md` will spell out exactly what.
- **Patch never breaks.** `0.x.Y` patches are always backwards compatible.
- We aim to give one minor cycle of deprecation warning where feasible, but it is not a guarantee until 1.0.

## Deprecation Policy (post-1.0)

1. The deprecated symbol/flag/key remains functional.
2. A `DeprecationWarning` (Python) or a stderr warning (CLI) is emitted.
3. Documentation marks it deprecated with the replacement and a planned removal version.
4. Removal is no sooner than the next `MAJOR` after the **next** minor release in which the deprecation was announced.

Example: deprecated in `1.4.0` → still works in `1.5.x` → may be removed in `2.0.0`.

## Long-Term Support (LTS)

- Until 1.0, only the latest minor receives fixes.
- After 1.0, we provide fixes for the **latest minor of each of the two most recent majors** (`N` and `N-1`) for at least **12 months** after the next major ships.
- Security fixes follow the same window with best-effort backports for older lines.

## Release Cadence

- **Patches:** as needed; no fixed schedule.
- **Minors:** roughly every **6–8 weeks** during active development.
- **Majors:** when necessary, ideally **≤ 1 / year**.
- **Pre-releases:** `X.Y.Z-rc.N` (release candidates), `X.Y.Z-beta.N`, `X.Y.Z-alpha.N` as needed.

## Tagging & Artifacts

- Git tags: `vX.Y.Z` (and `vX.Y.Z-rc.N`, etc.). Tags are signed (EP-0001B onwards).
- GitHub releases: one per tag, notes auto-generated from Conventional Commits, curated in `CHANGELOG.md`.
- PyPI: `eaip` package (and any subpackages) published with the same version.
- Container images: tagged with `X.Y.Z`, `X.Y`, `X`, and `latest` (latest stable).
- SBOMs (SPDX + CycloneDX) attached to each release (EP-0013).

## Yanked Releases

A release may be **yanked** (PyPI), **deprecated** (GitHub release marked as such), or removed from `latest` tags if it is found to be defective. We will:

- Publish an advisory with the affected versions and remediation.
- Cut a patch release with the fix.
- Leave the yanked artefact accessible for forensic purposes but no longer recommended.

## Migration Guides

For every breaking change (or any `MAJOR` bump, including pre-1.0 minors that break), we publish a migration guide in `docs/migrations/` linked from the release notes.

## Reference

- [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
