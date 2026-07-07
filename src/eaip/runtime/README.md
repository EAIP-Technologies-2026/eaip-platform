# `eaip.runtime`

Runtime engine components that bootstrap, host, and manage the application lifecycle.

| Module | Purpose |
| ------ | ------- |
| `bootstrap` | Application bootstrap and startup orchestration. |
| `builder` | Runtime configuration and component assembly. |
| `bus` | Message bus for inter-component communication. |
| `cache` | In-process caching for computed values. |
| `commands` | Command pattern for structured operations. |
| `composition` | Composition root wiring for the runtime. |
| `context` | Request-scoped context propagation. |
| `di` | Dependency injection integration for runtime components. |
| `events` | Event-driven communication between subsystems. |
| `exceptions` | Runtime-specific error types. |
| `graph` | Execution graph construction and traversal. |
| `health` | Runtime-level health indicators. |
| `hooks` | Lifecycle hook points for extension. |
| `host` | Long-running host process management. |
| `kernel` | Core runtime kernel dispatching work. |
| `kernel_events` | Kernel-level event definitions. |
| `loader` | Dynamic module and plugin loading. |
| `metrics` | Runtime telemetry and metrics collection. |
| `module` | Module abstraction for composable runtime units. |
| `pipeline` | Pipeline execution for sequential/parallel processing. |
| `plugin` | Plugin system for extensible runtime behaviour. |
| `queries` | Query pattern for structured data retrieval. |
| `registry` | Central registry for runtime components. |
| `scheduler` | Task scheduling and cron-like execution. |
| `workers` | Background worker pool management. |
