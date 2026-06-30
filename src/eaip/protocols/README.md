# `eaip.protocols`

Structural protocols expressing **shapes** that any class may implement
without inheritance.

| Protocol | Shape |
| -------- | ----- |
| `Startable` / `Stoppable` / `Disposable` | sync lifecycle hooks |
| `AsyncStartable` / `AsyncStoppable` / `AsyncDisposable` | async equivalents |
| `Healthcheckable` | `async check_health() -> HealthReport` |
| `Identifiable` / `Named` / `Versioned` | identity surface |

These complement (and do not replace) the abstract base classes in
[`eaip.interfaces`](../interfaces/README.md), which enforce a stricter
contract through inheritance.
