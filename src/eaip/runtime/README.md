# `eaip.runtime`

Runtime engine — kernel, modules, scheduler, context, and hooks.

Delivered by **EP-0002.2 (Bundle-008)** — Platform Kernel Engineering Pack.

## Implemented Modules

| Module | Purpose |
| ------ | ------- |
| `kernel` | `RuntimeKernel` — orchestrates platform lifecycle, modules, hooks, and scheduler. |
| `context` | `RuntimeContext` — typed, contextvar-based request-scoped context propagation. |
| `hooks` | `HookRegistry` — pre/post start/stop hook points with ordered execution. |
| `host` | `Host` + `run_forever()` — long-running host process with signal handling. |
| `module` | `RuntimeModule` protocol — contracts for pluggable runtime modules. |
| `scheduler` | `Scheduler` — background periodic and one-shot task scheduling. |

## Planned (Future EPs)

| Module | Purpose |
| ------ | ------- |
| `bootstrap` | Application bootstrap and startup orchestration. |
| `builder` | Runtime configuration and component assembly. |
| `bus` | Message bus for inter-component communication. |
| `cache` | In-process caching for computed values. |
| `commands` | Command pattern for structured operations. |
| `composition` | Composition root wiring for the runtime. |
| `di` | Dependency injection integration for runtime components. |
| `events` | Event-driven communication between subsystems. |
| `exceptions` | Runtime-specific error types. |
| `graph` | Execution graph construction and traversal. |
| `health` | Runtime-level health indicators. |
| `kernel_events` | Kernel-level event definitions. |
| `loader` | Dynamic module and plugin loading. |
| `metrics` | Runtime telemetry and metrics collection. |
| `pipeline` | Pipeline execution for sequential/parallel processing. |
| `plugin` | Plugin system for extensible runtime behaviour. |
| `queries` | Query pattern for structured data retrieval. |
| `registry` | Central registry for runtime components. |
| `workers` | Background worker pool management. |
