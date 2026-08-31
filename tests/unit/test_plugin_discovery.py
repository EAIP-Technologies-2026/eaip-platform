"""Tests for :mod:`eaip.plugins.discovery`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from eaip.plugins.discovery import PluginDiscovery
from eaip.plugins.plugin import Plugin, PluginManifest

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


@dataclass
class _SimplePlugin:
    manifest: PluginManifest

    async def activate(self, platform: Platform) -> None:
        pass

    async def deactivate(self, platform: Platform) -> None:
        pass


def _assert_is_plugin(obj: object) -> None:
    assert isinstance(obj, Plugin)


_SAMPLE_PLUGIN = _SimplePlugin(
    manifest=PluginManifest(name="sample", version="1.0.0"),
)


def test_discover_entry_points_none() -> None:
    d = PluginDiscovery()
    result = d.discover_entry_points("eaip.plugins.does_not_exist")
    assert result == []


class TestDiscoverModule:
    def test_empty_module(self) -> None:
        d = PluginDiscovery()
        result = d.discover_module("eaip.registry.registry")
        assert result == []

    def test_import_error(self) -> None:
        d = PluginDiscovery()
        result = d.discover_module("eaip._nonexistent_module_xyz")
        assert result == []


def test_discover_package_import_error() -> None:
    d = PluginDiscovery()
    result = d.discover_package("eaip._nonexistent_pkg_xyz")
    assert result == []


def test_protocol_isinstance_check() -> None:
    _assert_is_plugin(_SAMPLE_PLUGIN)
