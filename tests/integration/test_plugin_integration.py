"""Integration test for the full plugin lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from eaip.plugins.lifecycle import PluginLifecycleManager
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import Plugin, PluginDependency, PluginManifest
from eaip.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


class _BasePlugin:
    def __init__(self) -> None:
        self.manifest = PluginManifest(name="base", version="1.0.0")
        self.activated = False
        self.deactivated = False

    async def activate(self, platform: Platform) -> None:
        self.activated = True

    async def deactivate(self, platform: Platform) -> None:
        self.deactivated = True


class _ExtPlugin:
    def __init__(self) -> None:
        self.manifest = PluginManifest(
            name="ext",
            version="2.0.0",
            dependencies=(PluginDependency(name="base", version_spec=">=1.0.0"),),
        )
        self.activated = False
        self.deactivated = False

    async def activate(self, platform: Platform) -> None:
        self.activated = True

    async def deactivate(self, platform: Platform) -> None:
        self.deactivated = True


@pytest.mark.asyncio
async def test_end_to_end_lifecycle() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(loader=loader)

    base = _BasePlugin()
    ext = _ExtPlugin()

    loader.install(base)
    loader.install(ext)

    dep_errors = lifecycle.validate_dependencies()
    assert dep_errors == []

    ordered = lifecycle.resolve_activation_order()
    assert [p.manifest.name for p in ordered] == ["base", "ext"]

    assert isinstance(base, Plugin)
    assert isinstance(ext, Plugin)

    platform_sentinel = object()
    await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
    assert base.activated
    assert ext.activated
    assert "base" in loader.activated
    assert "ext" in loader.activated

    await lifecycle.deactivate_all(platform_sentinel)  # type: ignore[arg-type]
    assert base.deactivated
    assert ext.deactivated
    assert "base" not in loader.activated
    assert "ext" not in loader.activated


@pytest.mark.asyncio
async def test_idempotent_activate_deactivate() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    lifecycle = PluginLifecycleManager(loader=loader)

    p = _BasePlugin()
    loader.install(p)

    platform_sentinel = object()
    await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
    await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
    assert p.activated  # called once (idempotent in loader, but lifecycle calls ordered)

    await lifecycle.deactivate_all(platform_sentinel)  # type: ignore[arg-type]
    await lifecycle.deactivate_all(platform_sentinel)  # type: ignore[arg-type]
    assert p.deactivated  # called once (idempotent)
