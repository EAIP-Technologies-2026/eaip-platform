# EAIP Architecture

> **Status:** Foundational sketch (EP-0001A). Concrete contracts, schemas, and APIs land in EP-0002 onwards.
> **Audience:** maintainers, integrators, operators, security reviewers.
> **Last updated:** 2026-01-15

This document describes the **target architecture** of the Enterprise Autonomous Intelligence Platform. It is intentionally written ahead of the implementation so that every code change can be evaluated against a stable north star.

---

## Table of Contents

- [Goals & Non-Goals](#goals--non-goals)
- [System Overview](#system-overview)
- [Component Catalog](#component-catalog)
  - [Control Plane](#control-plane)
  - [Agent Runtime](#agent-runtime)
  - [Adapters](#adapters)
  - [Memory](#memory)
  - [Policy Engine](#policy-engine)
  - [Telemetry](#telemetry)
- [Data Model (Conceptual)](#data-model-conceptual)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
- [Deployment Topology](#deployment-topology)
- [Trust & Threat Model](#trust--threat-model)
- [Performance & Scaling](#performance--scaling)
- [Extensibility Contracts](#extensibility-contracts)
- [Glossary](#glossary)

---

## Goals & Non-Goals

### Goals

- **Production-grade agent orchestration** — reliability, observability, cost control.
- **Pluggable everything** — LLMs, tools, memory, policy, transports.
- **Strong typing & strict contracts** — Python `Protocol`s + Pydantic schemas.
- **Multi-tenant by default** — isolation of secrets, quotas, telemetry, and memory.
- **Replayable** — every run can be reconstructed deterministically (modulo LLM nondeterminism).

### Non-Goals (for v1)

- Replacing general-purpose workflow engines (Airflow, Temporal). EAIP integrates with them rather than competing.
- Hosting LLMs. EAIP is BYO-LLM; adapters call providers.
- Visual no-code authoring. CLI and SDK are first-class; UI is read-only at v1.
- Federated learning or model training.

## System Overview

```text
                         ┌────────────────────────────────────────────────┐
                         │                Operators / SDK / CLI           │
                         └────────────────────────────────────────────────┘
                                              │
                                  HTTPS / gRPC (mTLS, OIDC)
                                              │
┌────────────────────────────────────────────────────────────────────────────────┐
│                                CONTROL PLANE                                   │
│  Identity & RBAC · Tenants · Quotas · Policies · Audit Log · Admin API/UI      │
└────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                   internal RPC (mTLS)
                                              │
┌────────────────────────────────────────────────────────────────────────────────┐
│                                AGENT RUNTIME                                    │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Planner  │→ │ Router  │→ │ Executor │→ │ Guardrails│→ │ State / Memory  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
  ┌───────────┐    ┌───────────┐      ┌───────────┐      ┌───────────┐    ┌───────────┐
  │  LLMs     │    │  Tools    │      │  Memory   │      │  Policy   │    │ Telemetry │
  │ (OpenAI…) │    │ (HTTP/DB) │      │ (Redis…)  │      │  (OPA…)   │    │  (OTel)   │
  └───────────┘    └───────────┘      └───────────┘      └───────────┘    └───────────┘
```

## Component Catalog

### Control Plane

Stateless API service responsible for:

- **Identity & RBAC** — OIDC/JWT verification, role + scope checks.
- **Tenant management** — create/update/list, soft-delete, export.
- **Quotas** — token, tool-call, and request budgets per tenant/agent/key.
- **Policy bundles** — versioned policies, signed at publication.
- **Audit log** — append-only, exportable, tamper-evident hashes.

**Persistence:** PostgreSQL (config), object storage (audit log archives).

### Agent Runtime

Long-running service hosting active runs.

- **Planner** — produces a typed `Plan` from a `Goal`. Stateless; LLM-backed or rules-backed.
- **Router** — selects which `Tool` or `LLM` adapter handles each step; consults the Policy Engine.
- **Executor** — executes steps with retries, timeouts, idempotency keys, and circuit breakers.
- **Guardrails** — pre/post hooks for content filtering, PII redaction, and prompt sanitisation.
- **State / Memory** — short-term (run-scoped) and long-term (vector / relational) stores.

**Persistence:** Redis (run state, queues), PostgreSQL (durable run records), object storage (artifacts).

### Adapters

Adapters expose third-party capabilities through stable, typed contracts. The platform ships **reference adapters**; users add their own behind the same `Protocol`s.

| Kind   | Reference Implementations *(EP-0003/0005)*           |
| ------ | ----------------------------------------------------- |
| LLM    | OpenAI, Anthropic, Azure OpenAI, local (Ollama, vLLM) |
| Tool   | HTTP request, SQL query, file read, shell *(sandboxed)* |
| Memory | Redis (KV), Postgres+pgvector, Qdrant, in-memory     |

Each adapter declares: `name`, `version`, `capabilities`, `config schema`, `cost model`, `health check`.

### Memory

Two complementary layers:

- **Short-term memory (STM)** — per-run, ephemeral, fast (Redis). Holds the working context window, scratch-pads, and tool I/O history.
- **Long-term memory (LTM)** — per-tenant, durable, optionally vectorised. Holds curated facts, embeddings, and prior decisions.

A `MemoryStore` contract abstracts both. Access is **always tenant-scoped** at the adapter layer; cross-tenant access is impossible by construction.

### Policy Engine

Evaluates decisions at well-defined checkpoints:

1. **Pre-Plan** — is this goal allowed for this principal?
2. **Pre-Step** — is this tool/LLM allowed with this input?
3. **Post-Step** — is the output safe to retain / surface?
4. **Pre-Egress** — does the final response satisfy content & compliance policies?

Policies are expressed in a declarative DSL *(initial implementation may wrap OPA/Rego, decided in [DR-0003](DECISION_REGISTER.md#dr-0003))*. Bundles are signed and versioned; activation is auditable.

### Telemetry

- **Tracing** — OpenTelemetry spans for every plan, step, LLM/tool call. Trace IDs propagate end-to-end.
- **Logging** — structured (`structlog`), JSON output, redaction-aware.
- **Metrics** — Prometheus-compatible: latencies, token usage, error rates, budget burn-down.
- **Replay** — every span can be exported and re-executed against a frozen policy bundle.

## Data Model (Conceptual)

| Entity            | Purpose                                                |
| ----------------- | ------------------------------------------------------ |
| `Tenant`          | Isolation boundary; owns quotas, policies, memory.     |
| `Principal`       | A human, service, or agent acting within a Tenant.     |
| `AgentSpec`       | Versioned, declarative definition of an agent.         |
| `Run`             | A single execution of an `AgentSpec` with a `Goal`.    |
| `Step`            | A unit of work within a `Run` (tool/LLM/decision).     |
| `Artifact`        | Any byte-string produced/consumed by a `Step`.         |
| `PolicyBundle`    | Signed collection of policy rules.                     |
| `AuditEvent`      | Immutable record of a security-relevant action.        |

## Cross-Cutting Concerns

- **Configuration** — `pydantic-settings`; environment-first, validated at boot, never hot-mutated.
- **Concurrency** — `asyncio` for I/O; CPU-bound work runs in worker pools.
- **Idempotency** — every external side-effect carries a deterministic idempotency key.
- **Backpressure** — bounded queues at every async boundary; explicit shedding policies.
- **Time** — UTC everywhere; `datetime.now(timezone.utc)`; serialise as ISO-8601.
- **Errors** — typed exceptions; never swallow; always carry a stable `error_code`.

## Deployment Topology

EAIP is designed to run on Kubernetes; a single-node Docker Compose variant is provided for development.

```text
[Ingress] → [Control Plane (HPA)] ─┐
                                   ├─→ [PostgreSQL] [Redis] [Object Store]
[Ingress] → [Agent Runtime (HPA)] ─┘
                  │
                  └─→ External LLM / Tool providers
```

Recommended baselines (per cluster, will be refined post-load-tests):

- Control Plane: 3 replicas, 0.5–2 CPU, 512 MiB–2 GiB RAM.
- Agent Runtime: 3+ replicas, autoscaled on queue depth.
- PostgreSQL: managed service preferred; PITR enabled.
- Redis: managed service with persistence enabled for run state.

## Trust & Threat Model

Out-of-the-box threat model assumptions (full threat model in EP-0017):

- **Trusted:** EAIP code & images we publish, signed with cosign.
- **Semi-trusted:** Tenant administrators (can configure but not bypass policy bundles signed by a higher authority).
- **Untrusted:** End-user inputs, LLM outputs, third-party tool responses.

Top mitigations:

| Threat                                      | Mitigation                                              |
| ------------------------------------------- | ------------------------------------------------------- |
| Prompt injection via tool outputs           | Guardrails post-step; quarantine + structured tool I/O. |
| Secret exfiltration                         | Per-tenant secret stores; egress allow-listing.         |
| Cross-tenant data leakage                   | Tenant ID is a primary partition key; tested in CI.     |
| Cost overrun via runaway loops              | Token + step budgets enforced before each call.         |
| Supply-chain compromise                     | Pinned, hash-locked deps; SBOMs; signed releases.       |

## Performance & Scaling

- **Targets** *(SLOs finalised in EP-0018)*:
  - p95 orchestrator overhead per step: **< 25 ms** (excludes LLM/tool latency).
  - Throughput: **≥ 1,000 concurrent runs / 4-core runtime pod**.
  - Cold start: **< 3 s**.
- **Scaling axes:** stateless runtime replicas (horizontal), Redis cluster (sharded), per-tenant queue isolation.

## Extensibility Contracts

Every plugin point is a Python `Protocol` plus a Pydantic config schema. Stability is governed by `VERSIONING.md`. Indicative shape:

```python
class LLMAdapter(Protocol):
    name: str
    version: str

    async def complete(
        self, request: LLMRequest, *, context: RunContext
    ) -> LLMResponse: ...

    async def health(self) -> HealthReport: ...
```

Final contracts are introduced in EP-0003 (LLM), EP-0005 (Tools), and EP-0006 (Memory).

## Glossary

- **Agent** — a configured combination of planner, tools, memory, and policy that pursues goals.
- **Run** — one execution of an agent against a specific goal.
- **Step** — a single observable unit of work inside a run.
- **Adapter** — a plug-in that bridges EAIP and an external capability.
- **Tenant** — an isolation boundary for resources, policies, and data.
- **Guardrail** — a pre/post hook enforcing content, safety, or policy.
- **EP (Engineering Package)** — a planned, owned, versioned unit of platform work.
- **Foundation** — the reusable infrastructure layer (delivered by EP-0002) on which every capability is built.
- **Capability** — a self-describing, public unit of platform functionality (registered with the `CapabilityRegistry`).
- **Plugin** — a third-party extension satisfying the `Plugin` Protocol; installed into the `PluginRegistry`, activated by the `PluginLoader`.
- **Port** — an abstract dependency the platform needs from its host (e.g. `ClockPort`); implemented by an adapter under `eaip.infrastructure`.

---

## Platform Foundation Layout (EP-0002)

The Foundation source tree under `src/eaip/` is organised by **architectural
layer**, not by feature. Each package documents its own contract and exposes
a curated `__init__.py`. Layers depend strictly downward:

```text
                            ┌──────────────────────────────┐
                            │      application/            │   bootstrap + runner
                            └──────────────────────────────┘
                                          │
                            ┌──────────────────────────────┐
                            │      platform/               │   Platform + Builder (composition root)
                            └──────────────────────────────┘
                                          │
   ┌────────────┬─────────────┬───────────┴────────────┬──────────────┬────────────┐
   ▼            ▼             ▼                        ▼              ▼            ▼
lifecycle/  registry/   dependency_injection/    capabilities/    plugins/     core/
   │            │             │                        │              │            │
   └────────────┴─────────────┴────────────────────────┴──────────────┴────────────┘
                                          │
   ┌────────────┬─────────────┬───────────┴────────────┬──────────────┬────────────┐
   ▼            ▼             ▼                        ▼              ▼            ▼
events/     logging/      health/                   config/         settings/   factories/
                                          │
   ┌────────────┬─────────────┬───────────┴────────────┬──────────────┬────────────┐
   ▼            ▼             ▼                        ▼              ▼            ▼
serialization/ validation/  protocols/  interfaces/  metadata/    version/     utilities/
                                          │
                            ┌──────────────────────────────┐
                            │   ports/   ↔   infrastructure/   adapters/interfaces/
                            └──────────────────────────────┘
                                          │
                            ┌──────────────────────────────┐
                            │   shared/                    │   zero-dependency primitives
                            │   exceptions/                │
                            │   types/                     │
                            └──────────────────────────────┘
```

### Composition

A host obtains a fully-wired platform with one call:

```python
from eaip.application import build_platform, run_platform

async def main() -> None:
    platform = build_platform()
    await run_platform(platform)  # installs signal handlers; awaits shutdown
```

`build_platform()` performs the following in order:

1. Load `PlatformSettings` from `EAIP_*` env vars.
2. `configure_logging(settings.logging.to_logging_config())`.
3. Create the DI `Container`; wire the default port adapters (`SystemClock`, `UuidIdGenerator`, `EnvSecretProvider`).
4. Construct `EventBus`, `HealthReporter`, `LifecycleManager`, `CapabilityRegistry`, `PluginRegistry`, `PluginLoader`, `FeatureFlagRegistry`.
5. Register every subsystem instance back into the container so capabilities can resolve them.
6. Install (but **do not** activate) declared plugins.

`Platform.start()` then:

1. Binds `app`, `env`, `instance`, `version` into the structured-logging context.
2. Runs every `LifecycleManager` hook in registration order, rolling back on failure.
3. Activates every installed plugin (`PluginLoader.activate_all`).

`Platform.stop()` deactivates plugins in reverse, then runs lifecycle stop hooks LIFO — even if any step raises.

### Architectural Invariants

- The Foundation **never** imports from a capability pack. Dependency arrows always point **down** the layer diagram.
- All public symbols are typed; `mypy --strict` is the contract.
- No module performs I/O at import time.
- All timestamps are timezone-aware UTC; identifiers are typed `str` subclasses.
- Cross-cutting failures (DI cycles, registry conflicts, plugin contract violations) raise typed exceptions carrying stable `ErrorCode`s.

---

For history of architectural choices, see [`DECISION_REGISTER.md`](DECISION_REGISTER.md).
For risks affecting this architecture, see [`RISK_REGISTER.md`](RISK_REGISTER.md).
