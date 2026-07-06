"""Unit tests for :mod:`eaip.runtime.builder`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from eaip.application import build_platform
from eaip.runtime.builder import RuntimeBuilder
from eaip.runtime.context import RuntimeContext
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.kernel import RuntimeKernel
from eaip.runtime.module import BaseRuntimeModule

if TYPE_CHECKING:
    from eaip.runtime.host import RuntimeHost


class _TestModule(BaseRuntimeModule):
    module_name = "test-mod"

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


def test_builder_creates_kernel() -> None:
    platform = build_platform(configure_logging=False)
    kernel = RuntimeBuilder(platform).build()
    assert isinstance(kernel, RuntimeKernel)
    assert not kernel.is_running


def test_builder_with_module() -> None:
    platform = build_platform(configure_logging=False)
    kernel = RuntimeBuilder(platform).with_module(_TestModule()).build()
    assert "test-mod" in kernel.host.module_names


def test_builder_chaining() -> None:
    platform = build_platform(configure_logging=False)
    kernel = (
        RuntimeBuilder(platform)
        .with_module(_TestModule())
        .with_hooks(ObservabilityHooks())
        .build()
    )
    assert isinstance(kernel, RuntimeKernel)
    assert "test-mod" in kernel.host.module_names


# ---------------------------------------------------------------------------
# Bootstrap hooks
# ---------------------------------------------------------------------------


def test_builder_with_pre_start_hook() -> None:
    platform = build_platform(configure_logging=False)
    called = False

    def _pre(_k: object, _ctx: object) -> None:
        nonlocal called
        called = True

    kernel = (
        RuntimeBuilder(platform)
        .on_pre_start("test", _pre)
        .build()
    )
    assert kernel.bootstrap.pre_start_count == 1
    assert not called  # hook not executed yet


def test_builder_with_post_start_hook() -> None:
    platform = build_platform(configure_logging=False)
    kernel = (
        RuntimeBuilder(platform)
        .on_post_start("test", lambda _k, _ctx: None)
        .build()
    )
    assert kernel.bootstrap.post_start_count == 1


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


def test_builder_with_context() -> None:
    platform = build_platform(configure_logging=False)
    ctx = RuntimeContext.create(environment="test-custom")
    kernel = RuntimeBuilder(platform).with_context(ctx).build()
    assert isinstance(kernel, RuntimeKernel)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_builder_kernel_lifecycle() -> None:
    platform = build_platform(configure_logging=False)
    mod = _TestModule()
    kernel = RuntimeBuilder(platform).with_module(mod).build()

    assert not kernel.is_running
    assert not mod.started

    async with kernel:
        assert kernel.is_running
        assert mod.started

    assert not kernel.is_running
    assert mod.stopped


@pytest.mark.asyncio
async def test_builder_with_bootstrap_hooks_executed() -> None:
    pre_order: list[str] = []
    post_order: list[str] = []

    platform = build_platform(configure_logging=False)
    kernel = (
        RuntimeBuilder(platform)
        .with_module(_TestModule())
        .on_pre_start("pre", lambda _k, _ctx: pre_order.append("pre"))
        .on_post_start("post", lambda _k, _ctx: post_order.append("post"))
        .build()
    )

    async with kernel:
        assert pre_order == ["pre"]
        assert post_order == ["post"]


@pytest.mark.asyncio
async def test_builder_plugins_integrated() -> None:
    from dataclasses import dataclass, field
    from eaip.plugins import PluginManifest
    from eaip.plugins.loader import CURRENT_CONTRACT_VERSION
    from eaip.platform.platform import Platform

    @dataclass
    class _TestPlugin:
        manifest: PluginManifest
        activated: bool = field(default=False)
        deactivated: bool = field(default=False)

        async def activate(self, _platform: Platform) -> None:
            self.activated = True

        async def deactivate(self, _platform: Platform) -> None:
            self.deactivated = True

    plugin = _TestPlugin(
        manifest=PluginManifest(
            name="plugin-mod",
            version="1.0.0",
            contract_version=CURRENT_CONTRACT_VERSION,
        )
    )

    platform = build_platform(configure_logging=False)
    kernel = RuntimeBuilder(platform).with_plugin(plugin).build()

    assert "plugin-mod" in kernel.host.module_names

    async with kernel:
        assert plugin.activated

    assert plugin.deactivated
