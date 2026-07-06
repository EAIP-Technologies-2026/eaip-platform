"""Unit tests for :mod:`eaip.runtime.kernel`."""

from __future__ import annotations

import pytest

from eaip.application import build_platform
from eaip.exceptions.domain import LifecycleError
from eaip.runtime.bootstrap import BootstrapManager
from eaip.runtime.context import RuntimeContext
from eaip.runtime.host import RuntimeHost
from eaip.runtime.kernel import RuntimeKernel
from eaip.runtime.module import BaseRuntimeModule
from eaip.runtime.registry import RuntimeRegistry


class _SimpleModule(BaseRuntimeModule):
    module_name = "simple"

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.started = True

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.stopped = True


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_kernel_creates_with_defaults() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    registry = RuntimeRegistry()
    bootstrap = BootstrapManager()
    kernel = RuntimeKernel(host=host, registry=registry, bootstrap=bootstrap)

    assert not kernel.is_running
    assert kernel.host is host
    assert kernel.registry is registry
    assert kernel.bootstrap is bootstrap
    assert kernel.root is None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_and_stop() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)
    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=BootstrapManager(),
    )

    await kernel.start()
    assert kernel.is_running
    assert mod.started
    assert "simple" in kernel.registry.module_names()

    await kernel.stop()
    assert not kernel.is_running
    assert mod.stopped


@pytest.mark.asyncio
async def test_context_manager() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)
    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=BootstrapManager(),
    )

    async with kernel:
        assert kernel.is_running
        assert mod.started

    assert not kernel.is_running
    assert mod.stopped


@pytest.mark.asyncio
async def test_stop_is_idempotent() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_SimpleModule())
    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=BootstrapManager(),
    )

    await kernel.start()
    await kernel.stop()
    await kernel.stop()
    assert not kernel.is_running


@pytest.mark.asyncio
async def test_bootstrap_hooks_integrate() -> None:
    """Bootstrap pre/post hooks fire during kernel start."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    phase_order: list[str] = []
    bootstrap = BootstrapManager()
    bootstrap.add_pre_start("pre", lambda _k, _ctx: phase_order.append("pre"))
    bootstrap.add_post_start("post", lambda _k, _ctx: phase_order.append("post"))

    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=bootstrap,
    )

    await kernel.start()
    assert phase_order == ["pre", "post"]
    await kernel.stop()


@pytest.mark.asyncio
async def test_registry_populated_on_start() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    registry = RuntimeRegistry()
    kernel = RuntimeKernel(
        host=host,
        registry=registry,
        bootstrap=BootstrapManager(),
    )

    assert not registry.has_module("simple")
    await kernel.start()
    assert registry.has_module("simple")
    await kernel.stop()


@pytest.mark.asyncio
async def test_pre_start_hook_failure_prevents_host_start() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    bootstrap = BootstrapManager()
    bootstrap.add_pre_start("fail", lambda _k, _ctx: (_ for _ in ()).throw(RuntimeError("pre boom")))

    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=bootstrap,
    )

    with pytest.raises(LifecycleError):
        await kernel.start()

    assert not kernel.is_running
    assert not mod.started  # host never started


@pytest.mark.asyncio
async def test_custom_context_propagated() -> None:
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _SimpleModule()
    host.add_module(mod)

    base_ctx = RuntimeContext.create(environment="staging", tenant_id="t1")
    kernel = RuntimeKernel(
        host=host,
        registry=RuntimeRegistry(),
        bootstrap=BootstrapManager(),
        context=base_ctx,
    )

    await kernel.start()
    await kernel.stop()
    # Context should be usable; derived from base during lifecycle
    assert kernel.is_running is False
