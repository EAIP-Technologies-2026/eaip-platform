# EAIP Roadmap

> **Horizon:** rolling **4 quarters**, refreshed at the start of each quarter.
> **Last updated:** 2026-07-07
> **Owner:** Subham Panigrahi ([@subham1902](https://github.com/subham1902))

The roadmap is **directional**, not contractual. Priorities shift based on user feedback, technical discovery, and capacity. Significant changes are announced in [GitHub Discussions › Announcements](https://github.com/subham1902/eaip-platform/discussions/categories/announcements).

---

## Guiding Themes (2026)

1. **Foundation First** — quality gates, observability, and security before features.
2. **Composability** — every capability is a plug-in behind a stable contract.
3. **Operability** — designed for production from day one, not as an afterthought.
4. **Open by Default** — open contracts, open telemetry, open governance.

---

## Q2-Q3 2026 — Platform Foundation & Runtime (current)

| ID         | Deliverable                                | Status     | Owner        |
| ---------- | ------------------------------------------ | ---------- | ------------ |
| EP-0001A   | Repository foundation & governance         | ✅ Done    | @subham1902  |
| EP-0001B   | CI/CD baseline (matrix, caching, releases) | 🟡 Active  | @subham1902  |
| EP-0002    | Agent Runtime — core orchestrator skeleton | ✅ Done    | @subham1902  |
| EP-0002.2  | Platform Kernel (Bundle-008)               | ✅ Done    | @subham1902  |
| EP-0002.3  | Services & Application Layer (Bundle-009)  | ✅ Done    | @subham1902  |
| EP-0002.4  | Runtime Integration & Bootstrap (Bundle-010) | ✅ Done | @subham1902  |
| EP-0002.5  | Event Bus & Messaging Core (Bundle-011)      | ✅ Done | @subham1902  |
| EP-0002.6  | Registry & Plugin Runtime (Bundle-012)       | ✅ Done | @subham1902  |
| EP-0015    | Knowledge Engine (Bundle-016)                | ✅ Done | @subham1902  |
| EP-0003    | LLM Adapter contract + 2 reference adapters| ⚪ Planned | TBD          |
| EP-0004    | Telemetry baseline (OTel traces + structlog) | ⚪ Planned | TBD          |

**Exit criteria:** A "hello-world" agent can run end-to-end against one LLM adapter with traces emitted to OTel and structured logs to stdout.

## Q2 2026 — Composability

| ID         | Deliverable                                |
| ---------- | ------------------------------------------ |
| EP-0005    | Tool Adapter contract + HTTP/SQL reference tools |
| EP-0006    | Memory subsystem (short-term + vector backends) |
| EP-0007    | Policy Engine v1 (allow/deny lists, content filters) |
| EP-0008    | CLI (`eaip`) — agents, tools, runs, traces |
| EP-0009    | Cost & token-budget accounting             |

**Exit criteria:** Build a non-trivial agent (e.g., docs-Q&A) end-to-end using only stable contracts, with cost controls and policy enforcement.

## Q3 2026 — Operability

| ID         | Deliverable                                |
| ---------- | ------------------------------------------ |
| EP-0010    | Control Plane API (tenants, quotas, audit) |
| EP-0011    | Admin Web UI (read-only first)             |
| EP-0012    | Replay & evaluation harness                |
| EP-0013    | Container images, Helm chart, SBOM, cosign |
| EP-0014    | Reference Grafana / OTel dashboards        |

**Exit criteria:** Deploy a multi-tenant EAIP cluster on Kubernetes with full observability and a documented upgrade path.

## Q4 2026 — Hardening & 1.0 RC

| ID         | Deliverable                                |
| ---------- | ------------------------------------------ |
| EP-0015    | Public API stability review & freeze       |
| EP-0016    | Long-running soak tests + chaos suite      |
| EP-0017    | Threat model v1 + external pen-test        |
| EP-0018    | Performance baselines & SLOs               |
| EP-0019    | Migration guide for pre-1.0 users          |
| EP-0020    | **1.0.0-rc.1** release                     |

**Exit criteria:** A release candidate for `1.0.0` with documented SLOs, completed pen-test, and a clean upgrade story.

---

## Beyond 2026 (Aspirational)

- **Multi-runtime support** — Node.js and Go runtimes sharing the same contracts.
- **Agent marketplaces** — signed, versioned, discoverable agent & tool bundles.
- **Federated tenancy** — cross-cluster orchestration with policy federation.
- **Verifiable execution** — cryptographically attestable run logs for compliance.

## How to Influence the Roadmap

- 👍 React on roadmap discussions and feature requests — we read the signal.
- 📝 Open an [RFC discussion](https://github.com/subham1902/eaip-platform/discussions/categories/ideas) for substantial proposals.
- 🤝 Volunteer to own an EP — see [`ENGINEERING_TRACKER.md`](ENGINEERING_TRACKER.md) for unclaimed items.
- 💼 Sponsoring directed work? Contact `hello@eaip.dev`.

Status legend: ✅ Done · 🟡 Active · ⚪ Planned · ⏸ Paused · ❌ Dropped.
