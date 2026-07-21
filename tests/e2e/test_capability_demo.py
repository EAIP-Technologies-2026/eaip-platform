"""E2E demo — capability discovery, graph, health, and runtime integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from eaip.capabilities.capability import (
    Capability,
    CapabilityContract,
    CapabilityDependency,
    CapabilityStatus,
)
from eaip.capabilities.discovery import CapabilityDiscovery
from eaip.capabilities.events import CapabilityEnabled, CapabilityRegistered
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.health import CapabilityHealthCheck
from eaip.capabilities.registry import CapabilityRegistry
from eaip.capabilities.resolution import CapabilityResolver
from eaip.events.event import DomainEvent
from eaip.health.checks import HealthStatus
from eaip.plugins.plugin import PluginManifest
from eaip.runtime.capability_integration import CapabilityRuntimeModule

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


# ---------------------------------------------------------------------------
# Demo plugin stubs
# ---------------------------------------------------------------------------


@dataclass
class _Plugin:
    manifest: PluginManifest

    async def activate(self, platform: Platform) -> None:
        pass

    async def deactivate(self, platform: Platform) -> None:
        pass


# ---------------------------------------------------------------------------
# Integration test helpers
# ---------------------------------------------------------------------------


class _MockPlatform:
    def __init__(self) -> None:
        self._health_checks: dict[str, object] = {}
        self._plugins: list = []

    @property
    def health(self) -> object:
        class _Health:
            def __init__(self, checks: dict[str, object]) -> None:
                self._checks = checks

            def register(self, check: object) -> None:
                self._checks[getattr(check, "name", "unknown")] = check

        return _Health(self._health_checks)

    @property
    def plugin_loader(self) -> object:
        class _Loader:
            def __init__(self, plugins: list) -> None:
                self._plugins = plugins

            def all(self) -> list:
                return self._plugins

        return _Loader(self._plugins)

    def add_plugin(self, plugin: object) -> None:
        self._plugins.append(plugin)


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


@pytest.mark.asyncio
async def test_capability_demo_successful_lifecycle() -> None:
    """Demonstrate:
    1. Capability discovery from plugins
    2. Dependency graph construction
    3. Versioned resolution
    4. Health check
    """
    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery()

    plugin_metrics = _Plugin(
        PluginManifest(name="metrics", version="2.0.0", tags=("metrics.publish",)),
    )
    discovery.discover_from_plugin(plugin_metrics, registry)

    data_cap = Capability(
        name="data.ingest",
        title="Data Ingestion",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="metrics.publish"),),
        contract=CapabilityContract(contract_version="1.0.0"),
        metadata={"source": "demo"},
    )
    registry.register(data_cap)

    assert registry.has("metrics.publish")
    assert registry.has("data.ingest")

    graph = CapabilityGraph(registry.all())
    ordered = graph.topological_sort()
    assert ordered[0].name == "metrics.publish"
    assert ordered[-1].name == "data.ingest"

    resolver = CapabilityResolver()
    resolved = resolver.resolve(graph, "metrics.publish", ">=1.0.0")
    assert resolved is not None
    assert resolved.version == "2.0.0"

    unresolved = resolver.resolve(graph, "metrics.publish", ">=3.0.0")
    assert unresolved is None

    check = CapabilityHealthCheck(registry)
    report = await check.check()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_capability_demo_event_wiring() -> None:
    """Demonstrate capability events as proper DomainEvent subclasses."""
    evt = CapabilityRegistered(name="test.cap", version="1.0.0")
    assert isinstance(evt, DomainEvent)
    assert evt.name == "test.cap"

    evt2 = CapabilityEnabled(name="test.cap", version="1.0.0")
    assert isinstance(evt2, DomainEvent)


@pytest.mark.asyncio
async def test_capability_demo_runtime_integration() -> None:
    """Demonstrate CapabilityRuntimeModule start/stop."""
    registry = CapabilityRegistry()
    module = CapabilityRuntimeModule(registry)

    kernel = _MockKernel()
    kernel.platform.add_plugin(
        _Plugin(PluginManifest(name="demo", version="1.0.0", tags=("demo.cap",))),
    )

    await module.start(kernel)

    assert registry.has("demo.cap")
    cap = registry.get("demo.cap")
    assert cap.status is CapabilityStatus.ENABLED

    assert module.startup_duration > 0

    await module.stop(kernel)
    assert registry.get("demo.cap").status is CapabilityStatus.DISABLED
