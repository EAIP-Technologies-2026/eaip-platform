# `eaip.core`

Cross-cutting platform primitives that don't fit neatly elsewhere.

| Symbol | Purpose |
| ------ | ------- |
| `FeatureFlag` / `FeatureFlagRegistry` | Static feature flag definition + override resolution. |
| `ShutdownSignal` | `asyncio.Event` wrapper for coordinated graceful shutdown. |
| `install_shutdown_handlers` | Wire `SIGINT` / `SIGTERM` into a `ShutdownSignal`. |

Dynamic / runtime-toggleable feature flags arrive in a later engineering
package; the Foundation deliberately stays static and explicit.
