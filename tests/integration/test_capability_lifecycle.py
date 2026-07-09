"""Integration test for capability lifecycle — discovery, graph, resolution, health."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from eaip.capabilities.capability import Capability, CapabilityDependency, CapabilityStatus
from eaip.capabilities.discovery import CapabilityDiscovery
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.health import CapabilityHealthCheck
from eaip.capabilities.registry import CapabilityRegistry
from eaip.capabilities.resolution import CapabilityResolver
from eaip.health.checks import HealthStatus
from eaip.plugins.plugin import PluginManifest

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


@dataclass
class _Plugin:
    manifest: PluginManifest

    async def activate(self, platform: Platform) -> None:
        pass

    async def deactivate(self, platform: Platform) -> None:
        pass


@pytest.mark.asyncio
async def test_full_capability_lifecycle() -> None:
    """Demonstrate discovery -> graph -> resolve -> health check."""
    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery()

    p1 = _Plugin(PluginManifest(
        name="metrics-plugin",
        version="1.0.0",
        tags=("metrics.collect", "metrics.query"),
    ))
    p2 = _Plugin(PluginManifest(
        name="data-plugin",
        version="2.0.0",
        tags=("data.ingest",),
        provides_capabilities=(),
    ))

    discovery.discover_from_plugins([p1, p2], registry)

    assert registry.has("metrics.collect")
    assert registry.has("metrics.query")
    assert registry.has("data.ingest")

    # Register a dependent capability
    dep = Capability(
        name="dashboard.render",
        title="Dashboard Renderer",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="metrics.query"),),
    )
    registry.register(dep)

    graph = CapabilityGraph(registry.all())
    ordered = [c.name for c in graph.topological_sort()]
    assert "metrics.query" in ordered
    assert ordered[-1] == "dashboard.render"

    resolver = CapabilityResolver()
    resolved = resolver.resolve(graph, "metrics.query")
    assert resolved is not None
    assert resolved.name == "metrics.query"

    # Health check
    check = CapabilityHealthCheck(registry)
    report = await check.check()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_capability_dependency_failure() -> None:
    """Demonstrate unhealthy state from a cycle."""
    registry = CapabilityRegistry()
    a = Capability(
        name="a",
        title="A",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="b"),),
    )
    b = Capability(
        name="b",
        title="B",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="a"),),
    )
    registry.register(a)
    registry.register(b)

    with pytest.raises(Exception):
        CapabilityGraph(registry.all())


@pytest.mark.asyncio
async def test_capability_resolution_version_gate() -> None:
    """Demonstrate version-aware resolution."""
    registry = CapabilityRegistry()
    registry.register(Capability(name="svc", title="Svc", version="1.0.0"))
    graph = CapabilityGraph(registry.all())
    resolver = CapabilityResolver()

    assert resolver.resolve(graph, "svc", ">=0.5.0") is not None
    assert resolver.resolve(graph, "svc", ">=2.0.0") is None
