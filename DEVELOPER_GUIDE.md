# Developer Guide — Platform Foundation (EP-0002)

This guide is the **canonical reference** for engineers building on the EAIP
Platform Foundation. It complements the per-package READMEs under
`src/eaip/*/README.md` with end-to-end usage patterns.

---

## Table of Contents

- [Getting Started](#getting-started)
- [The Five-Minute Tour](#the-five-minute-tour)
- [Composing a Platform](#composing-a-platform)
- [Writing a Plugin](#writing-a-plugin)
- [Registering a Capability](#registering-a-capability)
- [Using the DI Container](#using-the-di-container)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Configuration & Settings](#configuration--settings)
- [Logging & Context](#logging--context)
- [Events](#events)
- [Health Checks](#health-checks)
- [Testing Your Capability](#testing-your-capability)
- [Style & Conventions](#style--conventions)
- [Reference](#reference)

---

## Getting Started

```bash
git clone https://github.com/subham1902/eaip-platform.git
cd eaip-platform
make bootstrap          # creates .venv, installs deps, installs pre-commit
make check              # ruff + black + mypy + pytest
```

Verify the Foundation is wired correctly:

```python
import asyncio
from eaip.application import build_platform

async def main():
    p = build_platform()
    async with p:
        print(p.name, p.version, p.phase)

asyncio.run(main())
```

## The Five-Minute Tour

Every long-running EAIP process boils down to:

```python
from eaip.application import build_platform, run_platform

async def main() -> None:
    platform = build_platform()
    await run_platform(platform)
```

`build_platform()` returns a `Platform` containing:

| Member | What lives there |
| ------ | ---------------- |
| `platform.container` | `Container` — DI bindings |
| `platform.lifecycle` | `LifecycleManager` — ordered startup/shutdown |
| `platform.events` | `EventBus` — in-process pub/sub |
| `platform.health` | `HealthReporter` — registered health checks |
| `platform.capabilities` | `CapabilityRegistry` — public capabilities |
| `platform.plugins` | `PluginRegistry` — installed plugins |
| `platform.plugin_loader` | `PluginLoader` — activation control |
| `platform.feature_flags` | `FeatureFlagRegistry` — static flag overlay |
| `platform.settings` | `PlatformSettings` — typed configuration |

## Composing a Platform

Use the **builder** when you need to inject plugins or override defaults:

```python
from eaip.platform import PlatformBuilder
from eaip.settings import load_platform_settings

platform = (
    PlatformBuilder()
    .with_settings(load_platform_settings())
    .with_plugin(my_plugin)
    .build()
)
```

To skip auto-configuring logging (e.g. when embedding the platform inside an
existing application):

```python
PlatformBuilder().without_logging_configuration().build()
```

## Writing a Plugin

A plugin is anything satisfying the `Plugin` Protocol — a `manifest` and two
async lifecycle methods.

```python
from dataclasses import dataclass, field
from eaip.plugins import PluginManifest

@dataclass
class HelloPlugin:
    manifest: PluginManifest = field(default_factory=lambda: PluginManifest(
        name="hello",
        version="0.1.0",
        description="A trivial demo plugin.",
    ))

    async def activate(self, platform) -> None:
        platform.capabilities.register(Capability(
            name="hello.world",
            title="Hello World",
            version="0.1.0",
        ))
        platform.events.subscribe(SomeDomainEvent, self._handle)

    async def deactivate(self, platform) -> None:
        platform.capabilities.unregister("hello.world")
```

Install with `PlatformBuilder.with_plugin(HelloPlugin())`. Plugins are
**activated** when the platform starts and **deactivated** in reverse order
when it stops. Activation is idempotent; the loader detects double-activate.

The **plugin contract version** is enforced at install time. Targeting a
different *major* contract raises `PluginContractViolationError` before any
user code runs.

## Registering a Capability

```python
from eaip.capabilities import Capability, CapabilityStatus

platform.capabilities.register(
    Capability(name="agent.run", title="Run Agent", version="1.0.0")
)
platform.capabilities.enable("agent.run")
```

Capabilities are **descriptors** (public contracts). The *implementation* of a
capability is wired into the DI container or registered with the event bus.

## Using the DI Container

```python
from eaip.dependency_injection import Container, Scope
from eaip.ports.clock import ClockPort

container: Container = platform.container

# Resolve a default-wired port
clock = container.resolve(ClockPort)

# Register your own service
class Greeter:
    def greet(self, who: str) -> str:
        return f"hello {who}"

container.register(Greeter, scope=Scope.SINGLETON)
greeter = container.resolve(Greeter)
```

Scopes:

- `SINGLETON` — built once per container (default).
- `TRANSIENT` — rebuilt on every resolution.
- `SCOPED` — one per child container created via `container.create_scope()`.

Cyclic dependencies raise `DependencyCycleError`; type mismatches raise
`RegistryTypeMismatchError`.

## Lifecycle Hooks

Anything that must start/stop in step with the platform belongs to the
`LifecycleManager`:

```python
async def open_db():  ...
async def close_db(): ...

platform.lifecycle.add("db", start=open_db, stop=close_db)
```

Hooks run in registration order on start, reverse order on stop. If a hook
fails during start, already-started hooks are stopped LIFO before the error
propagates.

## Configuration & Settings

For environment-only configuration use `PlatformSettings` directly:

```python
from eaip.settings import load_platform_settings
settings = load_platform_settings()
```

Environment variables follow the `EAIP_<SECTION>__<KEY>` pattern:

```text
EAIP_CORE__APP_NAME=my-service
EAIP_LOGGING__LEVEL=DEBUG
EAIP_FEATURE_FLAGS__ENABLED=["beta-routing"]
```

For arbitrary sources (files, dicts, layered), use `eaip.config`:

```python
from eaip.config import ConfigLoader, EnvSource, FileSource, LayeredSource

source = LayeredSource(
    FileSource("/etc/eaip/defaults.toml"),
    FileSource("/etc/eaip/overrides.toml", required=False),
    EnvSource(),
)
cfg = ConfigLoader(source).load(MyTypedModel)
```

## Logging & Context

Always use the platform logger — never `print`, never plain `logging`:

```python
from eaip.logging import get_logger, bind_context

log = get_logger(__name__)

bind_context(request_id="abc-123")
log.info("user.login.attempt", username="ada")
```

Sensitive keys (`password`, `token`, `secret`, ...) are redacted automatically
before render. Bound context propagates to every child logger and through
async tasks via `contextvars`.

## Events

```python
from eaip.events import DomainEvent

class UserSignedUp(DomainEvent):
    event_type = "user.signed_up"
    user_id: str

async def on_signup(evt: UserSignedUp) -> None:
    log.info("user.welcome_email_queued", user_id=evt.user_id)

platform.events.subscribe(UserSignedUp, on_signup)
await platform.events.publish(UserSignedUp(user_id="u-1"))
```

Handler failures never block other subscribers; failures are returned by
`publish()` for inspection.

## Health Checks

```python
from eaip.health import HealthReport, HealthStatus, callable_check

async def db_ping() -> HealthReport:
    ok = await db.ping()
    return HealthReport(
        component="db",
        status=HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY,
    )

platform.health.register(callable_check("db", db_ping))
report = await platform.health.report()
```

Worst-status wins in the rollup; failing checks are isolated.

## Testing Your Capability

Use the shipped fixtures:

```python
# tests/test_my_capability.py
import pytest
from tests.fixtures.platform import platform  # builder fixture

@pytest.mark.asyncio
async def test_my_capability(platform):
    async with platform:
        # arrange, act, assert against platform.capabilities / events / health
        ...
```

The platform is built **without** real logging configuration in tests
(`configure_logging=False`) so test output stays quiet by default.

## Style & Conventions

- Public symbols are fully typed. `Any` requires justification.
- No I/O at import time.
- All datetimes are timezone-aware UTC (`datetime.now(timezone.utc)`).
- Identifiers are typed `str` subclasses (`ComponentId`, `RunId`, ...).
- Errors are typed and carry stable `ErrorCode`s; never `except Exception:`
  without re-raising or logging.
- Public functions and classes carry Google-style docstrings.

## Reference

- **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Decisions:** [`DECISION_REGISTER.md`](DECISION_REGISTER.md)
- **Versioning:** [`VERSIONING.md`](VERSIONING.md)
- **Per-package docs:** every directory under `src/eaip/*/README.md`.
