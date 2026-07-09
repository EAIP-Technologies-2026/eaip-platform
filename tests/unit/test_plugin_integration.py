"""Tests for :mod:`eaip.runtime.plugin_integration`."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from eaip.health.checks import HealthStatus
from eaip.plugins.lifecycle import PluginLifecycleManager
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import PluginManifest
from eaip.plugins.registry import PluginRegistry
from eaip.runtime.plugin_integration import PluginHealthCheck, PluginRuntimeModule

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


class TestPluginHealthCheck:
    def test_no_plugins(self) -> None:
        reg = PluginRegistry()
        loader = PluginLoader(reg)
        lifecycle = PluginLifecycleManager(loader=loader)
        check = PluginHealthCheck(lifecycle)

        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY
        assert "no plugins installed" in report.message

    def test_all_activated(self) -> None:
        reg = PluginRegistry()
        loader = PluginLoader(reg)

        class _P:
            manifest: PluginManifest

            def __init__(self) -> None:
                self.manifest = PluginManifest(name="p1", version="1.0.0")

            async def activate(self, platform: Platform) -> None:
                pass

            async def deactivate(self, platform: Platform) -> None:
                pass

        p = _P()
        loader.install(p)
        loader._activated.add("p1")
        lifecycle = PluginLifecycleManager(loader=loader)
        check = PluginHealthCheck(lifecycle)

        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY
        assert "all" in report.message

    def test_degraded(self) -> None:
        reg = PluginRegistry()
        loader = PluginLoader(reg)

        class _P:
            manifest: PluginManifest

            def __init__(self) -> None:
                self.manifest = PluginManifest(name="p1", version="1.0.0")

            async def activate(self, platform: Platform) -> None:
                pass

            async def deactivate(self, platform: Platform) -> None:
                pass

        loader.install(_P())
        lifecycle = PluginLifecycleManager(loader=loader)
        check = PluginHealthCheck(lifecycle)

        report = asyncio.run(check.check())
        assert report.status is HealthStatus.DEGRADED
        assert "0/1" in report.message


class TestPluginRuntimeModule:
    def test_startup_duration_starts_zero(self) -> None:
        reg = PluginRegistry()
        loader = PluginLoader(reg)
        lifecycle = PluginLifecycleManager(loader=loader)
        platform_sentinel = object()
        mod = PluginRuntimeModule(lifecycle, platform_sentinel)  # type: ignore[arg-type]
        assert mod.startup_duration == 0.0
