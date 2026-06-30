# `eaip.health`

Lightweight health-check framework.

| Symbol | Purpose |
| ------ | ------- |
| `HealthStatus` | `healthy` / `degraded` / `unhealthy`. |
| `HealthReport` | Immutable Pydantic record (with nested `children` for rollups). |
| `HealthCheck` | Protocol: `name: str`, `async check() -> HealthReport`. |
| `HealthReporter` | Registers checks; `report()` runs them concurrently and aggregates worst-status semantics. |
| `callable_check(name, fn)` | Wrap an `async () -> HealthReport` into a `HealthCheck`. |

The reporter **isolates failures**: a check that raises is recorded as
`unhealthy` for that component without bringing down the rollup.
