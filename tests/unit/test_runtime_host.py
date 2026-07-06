"""Unit tests for :mod:`eaip.runtime.host`."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eaip.application import build_platform
from eaip.runtime.context import RuntimeContext, current_context
from eaip.runtime.exceptions import DependencyResolutionError, ModuleActivationError
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.host import RuntimeHost
from eaip.runtime.module import BaseRuntimeModule


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _SimpleModule(BaseRuntimeModule):
    module_name = "simple"

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.started = True

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.stopped = True


class _FailingStart(BaseRuntimeModule):
    module_name = "failing-start"

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        raise RuntimeError("intentional start failure")


class _FailingStop(BaseRuntimeModule):
    module_name = "failing-stop"

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.started = True

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.stopped = True
        raise RuntimeError("intentional stop failure")


class _WithDep(BaseRuntimeModule):
    module_name = "with-dep"
    module_dependencies = ("simple",)

    def __init__(self) -> None:
        self.started = False

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        # Assert that the dependency has already been started by the time we run.
        self.started = True


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_host_creates_with_defaults() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    assert not host.is_running
    assert host.module_names == []


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------


def test_add_module_registers_correctly() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_SimpleModule())
    assert "simple" in host.module_names


def test_get_module_returns_correct_instance() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    m = _SimpleModule()
    host.add_module(m)
    assert host.get_module("simple") is m


def test_get_module_returns_none_for_unknown() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    assert host.get_module("nope") is None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_and_stop_simple() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    await host.start()
    assert host.is_running
    assert mod.started

    await host.stop()
    assert not host.is_running
    assert mod.stopped


@pytest.mark.asyncio
async def test_context_manager() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    async with host:
        assert host.is_running

    assert not host.is_running
    assert mod.stopped


@pytest.mark.asyncio
async def test_dependency_ordering() -> None:
    """Modules start in dependency order."""
    order: list[str] = []

    class _A(BaseRuntimeModule):
        module_name = "a"

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            order.append("a")

    class _B(BaseRuntimeModule):
        module_name = "b"
        module_dependencies = ("a",)

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            order.append("b")

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_B())  # registered before A intentionally
    host.add_module(_A())

    await host.start()
    await host.stop()

    assert order.index("a") < order.index("b")


@pytest.mark.asyncio
async def test_start_failure_rolls_back() -> None:
    """When a module fails to start, already-started modules are stopped."""
    started: list[str] = []
    stopped: list[str] = []

    class _GoodA(BaseRuntimeModule):
        module_name = "good-a"

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            started.append("good-a")

        async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            stopped.append("good-a")

    class _FailsAfterA(BaseRuntimeModule):
        """Fails on start but declares dependency on good-a so it starts second."""

        module_name = "fails-after-a"
        module_dependencies = ("good-a",)

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            raise RuntimeError("intentional failure")

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_GoodA())
    host.add_module(_FailsAfterA())

    with pytest.raises(ModuleActivationError):
        await host.start()

    assert "good-a" in started
    assert "good-a" in stopped
    assert not host.is_running
    assert current_context() is None


@pytest.mark.asyncio
async def test_stop_failure_does_not_raise() -> None:
    """Stop failures are logged but do not propagate."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_FailingStop())

    await host.start()
    # Should complete without raising even though on_stop raises.
    await host.stop()
    assert not host.is_running


@pytest.mark.asyncio
async def test_stop_is_idempotent() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_SimpleModule())

    await host.start()
    await host.stop()
    await host.stop()  # second call — should be a no-op
    assert not host.is_running


@pytest.mark.asyncio
async def test_cyclic_dependency_raises_at_start() -> None:
    class _X(BaseRuntimeModule):
        module_name = "x"
        module_dependencies = ("y",)

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            pass

    class _Y(BaseRuntimeModule):
        module_name = "y"
        module_dependencies = ("x",)

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            pass

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_X())
    host.add_module(_Y())

    with pytest.raises(DependencyResolutionError):
        await host.start()


# ---------------------------------------------------------------------------
# Health integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_module_health_registered() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_SimpleModule())

    await host.start()
    assert "simple" in platform.health.registered()
    await host.stop()


# ---------------------------------------------------------------------------
# Observability hooks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hooks_fired() -> None:
    fired: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on_host_starting(lambda **_kw: fired.append("host_starting"))
    hooks.on_host_running(lambda **_kw: fired.append("host_running"))
    hooks.on_host_stopping(lambda **_kw: fired.append("host_stopping"))
    hooks.on_host_stopped(lambda **_kw: fired.append("host_stopped"))
    hooks.on_module_starting(lambda **_kw: fired.append("module_starting"))
    hooks.on_module_started(lambda **_kw: fired.append("module_started"))
    hooks.on_module_stopping(lambda **_kw: fired.append("module_stopping"))
    hooks.on_module_stopped(lambda **_kw: fired.append("module_stopped"))

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform, hooks=hooks)
    host.add_module(_SimpleModule())

    async with host:
        pass

    assert "host_starting" in fired
    assert "host_running" in fired
    assert "module_started" in fired
    assert "module_stopped" in fired
    assert "host_stopping" in fired
    assert "host_stopped" in fired


# ---------------------------------------------------------------------------
# Custom context
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_custom_base_context_propagated() -> None:
    """Modules receive a context derived from the host's base context."""
    received: list[RuntimeContext] = []

    class _CapturingMod(BaseRuntimeModule):
        module_name = "capturing"

        async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
            received.append(ctx)

    base = RuntimeContext.create(environment="test", tenant_id="tenant-1")
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform, context=base)
    host.add_module(_CapturingMod())

    await host.start()
    await host.stop()

    assert received
    ctx = received[0]
    assert ctx.environment == "test"
    assert ctx.tenant_id == "tenant-1"
    assert ctx.parent_run_id == base.run_id  # derived from base
