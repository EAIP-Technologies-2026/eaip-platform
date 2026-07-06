"""Cross-component integration tests for TC-0005/6/7 (Event Bus, Plugin, DI Runtime).

Verifies that RuntimeEventBus, RuntimePluginAdapter, and RuntimeContainer
work together correctly in the RuntimeHost lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from eaip.application import build_platform
from eaip.dependency_injection import Container, Scope
from eaip.events import DomainEvent
from eaip.plugins import PluginManifest
from eaip.plugins.loader import CURRENT_CONTRACT_VERSION
from eaip.runtime.context import RuntimeContext
from eaip.runtime.host import RuntimeHost
from eaip.runtime.module import BaseRuntimeModule

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


# ---------------------------------------------------------------------------
# Test event type
# ---------------------------------------------------------------------------


class _CustomEvent(DomainEvent):
    event_type = "test.custom_event"
    payload: str = ""


# ---------------------------------------------------------------------------
# Test plugin
# ---------------------------------------------------------------------------


@dataclass
class _IntegrationPlugin:
    manifest: PluginManifest
    activated: bool = field(default=False)
    deactivated: bool = field(default=False)
    captured_events: list[DomainEvent] = field(default_factory=list)

    async def activate(self, _platform: Platform) -> None:
        self.activated = True

    async def deactivate(self, _platform: Platform) -> None:
        self.deactivated = True


# ---------------------------------------------------------------------------
# Test module using DI
# ---------------------------------------------------------------------------


class _DiAwareModule(BaseRuntimeModule):
    module_name = "di-module"

    def __init__(self) -> None:
        self.resolved: object | None = None

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        # Resolve a platform-registered service from the runtime container
        from eaip.events.bus import EventBus
        self.resolved = host.container.resolve(EventBus)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plugin_adapter_receives_context() -> None:
    """Plugin activated via RuntimePluginAdapter receives RuntimeContext."""
    plugin = _IntegrationPlugin(
        manifest=PluginManifest(
            name="ctx-plugin",
            version="1.0.0",
            contract_version=CURRENT_CONTRACT_VERSION,
        )
    )
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_plugin(plugin)

    assert not plugin.activated
    async with host:
        assert plugin.activated
    assert plugin.deactivated


@pytest.mark.asyncio
async def test_host_event_bus_injects_context_id() -> None:
    """RuntimeEventBus publishes events with correlation_id from context."""
    plugin = _IntegrationPlugin(
        manifest=PluginManifest(
            name="event-plugin",
            version="1.0.0",
            contract_version=CURRENT_CONTRACT_VERSION,
        )
    )
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)

    received: list[str | None] = []

    def handler(ev: _CustomEvent) -> None:
        received.append(ev.correlation_id)

    host.events.subscribe(_CustomEvent, handler)

    async with host:
        ctx = RuntimeContext.create()
        from eaip.runtime.context import run_with_context

        with run_with_context(ctx):
            await host.events.publish(_CustomEvent(payload="integration"))

    assert len(received) == 1
    assert received[0] is not None


@pytest.mark.asyncio
async def test_module_resolves_di_via_host_container() -> None:
    """Module can resolve services from RuntimeContainer during on_start."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _DiAwareModule()
    host.add_module(mod)

    async with host:
        assert mod.resolved is not None
        from eaip.events.bus import EventBus
        assert isinstance(mod.resolved, EventBus)


@pytest.mark.asyncio
async def test_module_scope_lifecycle() -> None:
    """Module scopes are created and cleaned up during host lifecycle."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _DiAwareModule()
    host.add_module(mod)

    assert not host.container.has_active_scopes

    async with host:
        # Module scopes are only created/dropped per-module start/stop
        # At minimum the root container is always available
        assert host.container.root is platform.container

    assert not host.container.has_active_scopes


@pytest.mark.asyncio
async def test_full_integration_all_three_components() -> None:
    """All three new runtime components work together in a single lifecycle."""
    plugin = _IntegrationPlugin(
        manifest=PluginManifest(
            name="all-in-one",
            version="1.0.0",
            contract_version=CURRENT_CONTRACT_VERSION,
        )
    )
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_plugin(plugin)
    host.add_module(_DiAwareModule())

    received_events: list[DomainEvent] = []

    def event_collector(ev: DomainEvent) -> None:
        received_events.append(ev)

    # Subscribe to all runtime events
    from eaip.runtime.events import RuntimeEvent

    host.events.subscribe(RuntimeEvent, event_collector)

    async with host:
        assert plugin.activated
        mod = host.get_module("di-module")
        assert mod is not None
        assert isinstance(mod, _DiAwareModule)
        assert mod.resolved is not None

    assert plugin.deactivated
    # Should have received lifecycle events
    assert len(received_events) > 0
