# `eaip.runtime` — Runtime Kernel

**Layer 2** of the EAIP architecture (above the Foundation, below Capabilities).

## What this package provides

| Component | Description |
|-----------|-------------|
| `RuntimeContext` | Immutable, contextvars-propagated execution context (run\_id, trace\_id, tenant\_id, …) |
| `RuntimeModule` / `BaseRuntimeModule` | Protocol + base class for kernel modules |
| `RuntimeHost` | Orchestrates ordered module startup, shutdown, and rollback |
| `ModuleLoader` | Validates and stores modules before activation |
| `DependencyGraph` | Kahn topological sort for dependency-ordered startup |
| `RuntimeHealthCheck` | Adapts module `check_health()` to the `HealthCheck` protocol |
| `ObservabilityHooks` | Synchronous hooks at every lifecycle boundary |
| `runtime.events` | Typed `DomainEvent` subclasses published on the platform `EventBus` |
| `runtime.exceptions` | Runtime-specific exception hierarchy (`EAIP-0012` — `EAIP-0016`) |

## Quick start

```python
from eaip.application import build_platform
from eaip.runtime import BaseRuntimeModule, RuntimeContext, RuntimeHost

class MyModule(BaseRuntimeModule):
    module_name = "my-module"

    async def on_start(self, host, ctx: RuntimeContext) -> None:
        ...  # connect to resources, register capabilities, etc.

    async def on_stop(self, host, ctx: RuntimeContext) -> None:
        ...  # release resources


platform = build_platform()
host = RuntimeHost(platform=platform)
host.add_module(MyModule())

async with platform:
    async with host:
        ...  # modules are running
```

## Dependency ordering

Modules declare their dependencies by name:

```python
class B(BaseRuntimeModule):
    module_name = "b"
    module_dependencies = ("a",)  # B starts after A
```

Unknown or cyclic dependencies raise `DependencyResolutionError` at start time.

## Health integration

Every `BaseRuntimeModule` automatically exposes its `check_health()` result
in the platform health rollup once the host starts.  Override `check_health()`
in your module to provide real checks:

```python
async def check_health(self) -> HealthReport:
    if self._is_connected():
        return HealthReport(component=self.name, status=HealthStatus.HEALTHY)
    return HealthReport(component=self.name, status=HealthStatus.UNHEALTHY,
                        message="not connected")
```

## Observability hooks

```python
hooks = ObservabilityHooks()
hooks.on_module_started(lambda module, ctx: metrics.increment("module.started"))
host = RuntimeHost(platform=platform, hooks=hooks)
```
