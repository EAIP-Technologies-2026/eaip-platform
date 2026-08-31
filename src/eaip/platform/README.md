# `eaip.platform`

The top-level **composition root** that ties every Foundation layer together.

```python
from eaip.platform import PlatformBuilder

platform = PlatformBuilder().with_plugin(my_plugin).build()

async with platform:
    # platform is running; capabilities, events, health are all live
    ...
```

The `Platform` object exposes read-only access to:

| Property | Subsystem |
| -------- | --------- |
| `container` | DI `Container` |
| `lifecycle` | `LifecycleManager` |
| `events` | `EventBus` |
| `health` | `HealthReporter` |
| `capabilities` | `CapabilityRegistry` |
| `plugins` | `PluginRegistry` |
| `plugin_loader` | `PluginLoader` |
| `feature_flags` | `FeatureFlagRegistry` |
| `settings` | `PlatformSettings` |
| `phase` | Current `LifecyclePhase` |

`Platform` is an **async context manager** — entering calls `start()`,
exiting calls `stop()` (plugin deactivation + lifecycle rollback).
