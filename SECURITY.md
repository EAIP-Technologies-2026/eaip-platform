# Security Policy

The EAIP team and community take security seriously. We appreciate responsible disclosure of vulnerabilities and will work with you to verify, fix, and credit your findings.

---

## Supported Versions

Security fixes are provided for the **latest minor release** of each supported major version. Older releases receive fixes only for **critical** vulnerabilities on a best-effort basis.

| Version  | Supported          | Notes                              |
| -------- | ------------------ | ---------------------------------- |
| `0.x`    | :white_check_mark: | Active development (pre-1.0)       |
| `< 0.1`  | :x:                | Foundation only — no runtime yet   |

Once `1.0.0` ships, this table will reflect the standard `N` and `N-1` minor-version support window described in [`VERSIONING.md`](VERSIONING.md).

## Reporting a Vulnerability

**Please do not file public GitHub issues for security vulnerabilities.**

We accept reports via either of the following channels:

1. **GitHub Private Vulnerability Reporting** *(preferred)* —
   <https://github.com/subham1902/eaip-platform/security/advisories/new>
2. **Email** — `security@eaip.dev`
   - PGP encryption available — fingerprint published at
     <https://eaip.dev/.well-known/security.txt> *(populated in EP-0002).*

Please include as much of the following as you can:

- A clear, concise description of the issue and its security impact.
- The component, file, function, or endpoint affected (and version/commit).
- A minimal reproducer (PoC code, request payload, or step-by-step).
- Your assessment of severity (CVSS v3.1 vector welcome but not required).
- Whether the vulnerability is already known publicly.
- Suggested remediation, if any.
- How you would like to be credited (or whether you prefer to remain anonymous).

## Our Commitment

| Stage                     | Target SLA *(business days)* |
| ------------------------- | ---------------------------- |
| Acknowledgement           | **≤ 2**                      |
| Triage & severity rating  | **≤ 5**                      |
| Status update cadence     | **every 7 days**             |
| Fix / mitigation released | **≤ 90 days** (critical: ≤ 30) |

We commit to:

- Treating your report confidentially until a coordinated disclosure date.
- Keeping you informed at each stage.
- Crediting you in the advisory and `CHANGELOG.md` (unless you opt out).
- **Not** pursuing legal action for good-faith research conducted under this policy.

## Safe Harbor

We consider security research conducted under this policy to be:

- Authorized concerning any applicable anti-hacking laws.
- Authorized concerning any relevant anti-circumvention laws.
- Exempt from restrictions in our Terms of Service that would interfere with conducting security research.
- Lawful, helpful to the overall security of the Internet, and conducted in good faith.

You are expected, as always, to comply with all applicable laws. If at any time you have concerns or are uncertain whether your security research is consistent with this policy, please contact `security@eaip.dev` **before** going further.

## Scope

The following are **in scope**:

- All source code under this repository.
- Official release artifacts (PyPI wheels, container images) published from this repository.
- Documented configuration defaults shipped in this repository.

The following are **out of scope** (but still appreciated as bug reports):

- Vulnerabilities in third-party dependencies (please report them to the upstream project; we will coordinate updates).
- Issues requiring physical access, root on the host, or already-compromised credentials.
- Social engineering of maintainers.
- Denial of service via volumetric attacks against community infrastructure (e.g., GitHub).
- Findings from automated scanners without a demonstrated exploitable impact.

## Coordinated Disclosure

We follow a **90-day coordinated disclosure window** by default. The clock starts when we acknowledge your report. We may request an extension for complex issues; we will also accelerate if a vulnerability is being actively exploited.

After a fix is released, we publish a **GitHub Security Advisory** (and CVE where applicable), update `CHANGELOG.md`, and notify users via release notes.

## Hardening Practices

EAIP is engineered with the following baselines (tracked & expanded in [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`RISK_REGISTER.md`](RISK_REGISTER.md)):

- Least-privilege defaults across services and tenants.
- Secrets are **never** stored in source, logs, or telemetry. Pre-commit hook scans for secrets.
- All CI workflows are pinned by **SHA**, run with `permissions: read-all` by default, and never expose tokens to forks.
- Dependencies are scanned by `pip-audit` (Python) and `osv-scanner` (transitive) on every PR.
- Static analysis: `bandit`, `ruff` security rules, `semgrep` *(EP-0003)*.
- Container images: scanned by `trivy`, signed with `cosign` *(EP-0004)*.
- SBOMs generated per release in SPDX & CycloneDX formats *(EP-0004)*.

## Acknowledgements

A public Hall of Fame for security researchers will be maintained at
<https://eaip.dev/security/hall-of-fame> *(seeded in EP-0002)*.

Thank you for helping keep EAIP and its users safe.
