"""Tests for :mod:`eaip.capabilities.discovery`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from eaip.capabilities.discovery import CapabilityDiscovery
from eaip.capabilities.registry import CapabilityRegistry
from eaip.plugins.plugin import PluginManifest

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


@dataclass
class _TestPlugin:
    manifest: PluginManifest

    async def activate(self, platform: Platform) -> None:
        pass

    async def deactivate(self, platform: Platform) -> None:
        pass


def test_discover_from_plugin_tags() -> None:
    manifest = PluginManifest(
        name="test-plugin",
        version="1.0.0",
        tags=("cap1", "cap2"),
    )
    plugin = _TestPlugin(manifest=manifest)
    discovery = CapabilityDiscovery()
    registry = CapabilityRegistry()

    caps = discovery.discover_from_plugin(plugin, registry)
    assert len(caps) == 2
    assert registry.has("cap1")
    assert registry.has("cap2")
    assert registry.get("cap1").metadata.get("plugin") == "test-plugin"


def test_discover_from_plugin_provides_capabilities() -> None:
    manifest = PluginManifest(
        name="test-plugin",
        version="1.0.0",
        provides_capabilities=("custom.cap",),
    )
    plugin = _TestPlugin(manifest=manifest)
    discovery = CapabilityDiscovery()
    registry = CapabilityRegistry()

    caps = discovery.discover_from_plugin(plugin, registry)
    assert len(caps) == 1
    assert caps[0].name == "custom.cap"
    assert caps[0].version == "1.0.0"


def test_discover_from_plugin_no_capabilities() -> None:
    manifest = PluginManifest(name="empty", version="1.0.0")
    plugin = _TestPlugin(manifest=manifest)
    discovery = CapabilityDiscovery()
    registry = CapabilityRegistry()

    caps = discovery.discover_from_plugin(plugin, registry)
    assert caps == []


def test_discover_from_plugins_multiple() -> None:
    p1 = _TestPlugin(
        manifest=PluginManifest(name="p1", version="1.0.0", tags=("alpha",)),
    )
    p2 = _TestPlugin(
        manifest=PluginManifest(name="p2", version="2.0.0", tags=("beta",)),
    )
    discovery = CapabilityDiscovery()
    registry = CapabilityRegistry()

    caps = discovery.discover_from_plugins([p1, p2], registry)
    assert len(caps) == 2
    assert registry.has("alpha")
    assert registry.has("beta")


def test_discover_replace_existing() -> None:
    manifest = PluginManifest(name="test", version="1.0.0", tags=("cap",))
    plugin = _TestPlugin(manifest=manifest)
    discovery = CapabilityDiscovery()
    registry = CapabilityRegistry()

    discovery.discover_from_plugin(plugin, registry)
    # Re-register with replace
    caps = discovery.discover_from_plugin(plugin, registry, replace=True)
    assert len(caps) == 1
