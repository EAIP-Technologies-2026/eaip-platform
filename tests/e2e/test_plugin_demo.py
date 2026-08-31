"""E2E demo — plugin lifecycle, dependency validation, and runtime integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from eaip.exceptions.domain import PluginError
from eaip.health.checks import HealthStatus
from eaip.plugins.dependency import PluginDependencyValidator
from eaip.plugins.lifecycle import PluginLifecycleManager
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import PluginDependency, PluginManifest
from eaip.plugins.registry import PluginRegistry
from eaip.runtime.plugin_integration import PluginHealthCheck

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


class _MetricsPlugin:
    """A simulated metrics-collection plugin."""

    def __init__(self) -> None:
        self.manifest = PluginManifest(
            name="metrics",
            version="1.0.0",
            description="Collects and exposes metrics",
            tags=("metrics", "observability"),
        )
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    async def activate(self, platform: Platform) -> None:
        self._started = True

    async def deactivate(self, platform: Platform) -> None:
        self._started = False


class _DataPlugin:
    """A simulated data-ingestion plugin that depends on metrics."""

    def __init__(self) -> None:
        self.manifest = PluginManifest(
            name="data",
            version="2.0.0",
            description="Ingests and processes data",
            dependencies=(PluginDependency(name="metrics", version_spec=">=1.0.0"),),
            tags=("data", "ingestion"),
        )
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    async def activate(self, platform: Platform) -> None:
        self._started = True

    async def deactivate(self, platform: Platform) -> None:
        self._started = False


class _BadPlugin:
    """A plugin that fails to activate."""

    def __init__(self) -> None:
        self.manifest = PluginManifest(name="bad", version="0.1.0")

    async def activate(self, platform: Platform) -> None:
        raise RuntimeError("activation failure")

    async def deactivate(self, platform: Platform) -> None:
        pass


@pytest.mark.asyncio
async def test_plugin_demo_successful_lifecycle() -> None:
    """Demonstrate a successful plugin lifecycle with dependency validation."""
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(
        loader=loader,
        validator=PluginDependencyValidator(),
    )

    metrics = _MetricsPlugin()
    data = _DataPlugin()
    loader.install(metrics)
    loader.install(data)

    dep_errors = lifecycle.validate_dependencies()
    assert dep_errors == []

    ordered = lifecycle.resolve_activation_order()
    assert [p.manifest.name for p in ordered] == ["metrics", "data"]

    platform_sentinel = object()
    await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
    assert metrics.started
    assert data.started

    await lifecycle.deactivate_all(platform_sentinel)  # type: ignore[arg-type]
    assert not metrics.started
    assert not data.started


@pytest.mark.asyncio
async def test_plugin_demo_health_check() -> None:
    """Demonstrate plugin health check reporting."""
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(loader=loader)

    check = PluginHealthCheck(lifecycle)

    report = await check.check()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_plugin_demo_activation_failure() -> None:
    """Demonstrate lifecycle handling of a failing plugin."""
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(loader=loader)

    bad = _BadPlugin()
    loader.install(bad)
    loader.install(_MetricsPlugin())

    platform_sentinel = object()
    with pytest.raises(PluginError, match="1 plugin"):
        await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_plugin_demo_partial_activation() -> None:
    """Demonstrate that all-or-nothing activation raises on any failure."""
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(loader=loader)

    loader.install(_BadPlugin())
    platform_sentinel = object()
    with pytest.raises(PluginError, match="1 plugin"):
        await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
