# Risk Register

> **Purpose:** Track risks that could materially affect EAIP — engineering, operational, security, legal, and community.
> **Convention:** Each risk has an **owner**, a **likelihood**, an **impact**, a **score** (L × I), and a **mitigation plan**.
> **Review cadence:** monthly; before every major release.
> **Last updated:** 2026-01-15

---

## Scoring Rubric

| Likelihood (L) | Definition                          | Impact (I) | Definition                                  |
| -------------- | ----------------------------------- | ---------- | ------------------------------------------- |
| 1 — Rare       | Unlikely within the next year       | 1 — Minor  | Localised, easy workaround                  |
| 2 — Unlikely   | Possible but not expected           | 2 — Low    | Slows a team / non-critical degradation     |
| 3 — Possible   | Could happen this quarter           | 3 — Moderate | Breaks a feature for some users           |
| 4 — Likely     | Expected this quarter               | 4 — High   | Outage, data loss for a tenant              |
| 5 — Almost certain | Already occurring or imminent   | 5 — Severe | Multi-tenant outage / breach / legal harm   |

**Score = L × I.** Treat ≥ 12 as *Critical* — mitigation must have a named owner and a due date.

---

## Active Risks

| ID      | Risk                                                     | Category   | L | I | Score | Status     | Owner       |
| ------- | -------------------------------------------------------- | ---------- | - | - | ----- | ---------- | ----------- |
| R-0001  | Onboarding friction discourages contributors             | Community  | 3 | 3 | 9     | Mitigating | @subham1902 |
| R-0002  | Supply-chain compromise (dependency, build, registry)    | Security   | 2 | 5 | 10    | Mitigating | @subham1902 |
| R-0003  | Single-maintainer bus factor                             | Org        | 3 | 5 | 15    | Open       | @subham1902 |
| R-0004  | Prompt-injection via tool/LLM outputs                    | Security   | 4 | 4 | 16    | Planned    | TBD         |
| R-0005  | Cost overruns from runaway LLM/tool loops                | Operational| 4 | 3 | 12    | Planned    | TBD         |
| R-0006  | Cross-tenant data leakage                                | Security   | 2 | 5 | 10    | Planned    | TBD         |
| R-0007  | Upstream LLM API breaking changes                        | External   | 4 | 3 | 12    | Mitigating | @subham1902 |
| R-0008  | Regulatory shift (AI Act, sectoral rules) before 1.0     | Legal      | 3 | 3 | 9     | Monitoring | @subham1902 |
| R-0009  | Premature 1.0 freezes immature APIs                      | Product    | 3 | 4 | 12    | Mitigating | @subham1902 |
| R-0010  | CI minutes / infra cost exceed sustainable budget        | Operational| 3 | 2 | 6     | Monitoring | @subham1902 |

Status legend: **Open · Planned · Mitigating · Mitigated · Accepted · Realised**.

## Retired / Realised Risks

| ID | Risk | Outcome | Date |
| -- | ---- | ------- | ---- |
| —  | —    | —       | —    |

---

## Detail

### R-0001 — Onboarding friction discourages contributors

- **Description:** New contributors abandon if setup, expectations, or first review take too long.
- **Mitigation:** `make bootstrap` < 2 min on a fresh machine; `CONTRIBUTING.md` outlines the workflow; PR template makes expectations explicit; review SLA in `CONTRIBUTING.md`.
- **Indicators:** time-to-first-PR-merge, % of PRs with > 3 review rounds.

### R-0002 — Supply-chain compromise

- **Description:** Compromised dependency, build infrastructure, or release registry could push malicious code to users.
- **Mitigation:** Pinned versions, hash-locked installs *(EP-0001B)*, `pip-audit` + `osv-scanner` in CI, signed releases *(EP-0013)*, branch protection + required reviews, GitHub Actions pinned by SHA, `permissions: read-all` default.
- **Indicators:** number of unpinned actions, mean dependency lag, audit findings.

### R-0003 — Single-maintainer bus factor

- **Description:** Project halts if the sole maintainer becomes unavailable.
- **Mitigation:** Recruit ≥ 2 maintainers within 2 quarters; explicit governance in `CONTRIBUTING.md`; offline-readable runbooks; private key custody documented.
- **Indicators:** # active maintainers, # CODEOWNERS entries.

### R-0004 — Prompt-injection via tool/LLM outputs

- **Description:** Malicious content in tool responses (e.g., scraped web pages) hijacks the agent.
- **Mitigation:** Guardrails at Pre-Step and Post-Step, structured (typed) tool I/O, quarantine of untrusted strings, egress allow-listing, deterministic re-planning rules. Tracked in EP-0007 and EP-0017.
- **Indicators:** # injection findings in red-team exercises, false-positive rate of guardrails.

### R-0005 — Cost overruns from runaway loops

- **Description:** Pathological plans burn tokens / tool calls until exhausted.
- **Mitigation:** Per-tenant and per-run **token + step budgets** enforced before each call; circuit breakers; cost dashboards; alerts on budget burn-down. EP-0009.
- **Indicators:** mean tokens/run, max tokens/run, # budget-tripped events.

### R-0006 — Cross-tenant data leakage

- **Description:** A defect or misconfiguration exposes one tenant's data to another.
- **Mitigation:** Tenant ID is a primary partition key; all adapters require `tenant_id` at the call boundary; multi-tenant invariant tests in CI; periodic schema audits.
- **Indicators:** # multi-tenant invariant tests, # high-severity SAST findings touching adapters.

### R-0007 — Upstream LLM API breaking changes

- **Description:** Provider sunsets a model or changes response shapes, breaking adapters.
- **Mitigation:** Adapter contracts isolate providers; integration tests pinned to provider SDKs; provider release-monitoring; multi-provider failover where applicable.
- **Indicators:** # provider deprecation notices outstanding.

### R-0008 — Regulatory shift before 1.0

- **Description:** New AI-specific regulation (EU AI Act, sectoral guidance) introduces obligations EAIP cannot meet at 1.0.
- **Mitigation:** Track regulatory developments; design for auditability and consent now; engage external counsel before 1.0.
- **Indicators:** # open regulatory gaps in compliance matrix.

### R-0009 — Premature 1.0 freezes immature APIs

- **Description:** Releasing 1.0 too early locks in regrettable contracts.
- **Mitigation:** EP-0015 API stability review; explicit "experimental" markers on unstable APIs; deprecation policy in `VERSIONING.md`.
- **Indicators:** # APIs marked experimental at 1.0 RC.

### R-0010 — CI / infra costs exceed budget

- **Description:** Test matrix expands and CI minutes / artefact storage drive unsustainable cost.
- **Mitigation:** Path-filtered workflows, aggressive caching, sparse matrices on non-default branches, self-hosted runners if needed.
- **Indicators:** monthly CI cost, mean CI duration.

---

## Adding a New Risk

1. Append a row to **Active Risks** and a section below.
2. Score honestly — over-scoring trivialises real risks.
3. A risk without indicators is a risk you cannot track. Always include them.
4. When closed, move the row to **Retired / Realised Risks**; do **not** delete.
