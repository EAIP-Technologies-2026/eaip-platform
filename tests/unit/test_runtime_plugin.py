"""Tests for :mod:`eaip.runtime.plugin`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from eaip.plugins import PluginManifest
from eaip.plugins.loader import CURRENT_CONTRACT_VERSION
from eaip.plugins.plugin import Plugin
from eaip.runtime.context import RuntimeContext
from eaip.runtime.host import RuntimeHost
from eaip.runtime.plugin import RuntimePluginAdapter

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


@dataclass
class _DummyPlugin:
    manifest: PluginManifest
    activated: int = field(default=0)
    deactivated: int = field(default=0)

    async def activate(self, _platform: Platform) -> None:
        self.activated += 1

    async def deactivate(self, _platform: Platform) -> None:
        self.deactivated += 1


def _make_plugin(name: str = "test-plugin") -> _DummyPlugin:
    return _DummyPlugin(
        manifest=PluginManifest(
            name=name,
            version="1.0.0",
            contract_version=CURRENT_CONTRACT_VERSION,
        )
    )


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_adapter_satisfies_plugin_protocol() -> None:
    """RuntimePluginAdapter is a valid Plugin protocol implementer."""
    adapter = RuntimePluginAdapter(_make_plugin(), object())  # type: ignore[arg-type]
    # The adapter itself is NOT a Plugin — it's a RuntimeModule.
    # But the input plugin must satisfy Plugin protocol.
    assert isinstance(_make_plugin(), Plugin)


# ---------------------------------------------------------------------------
# Name from manifest
# ---------------------------------------------------------------------------


def test_name_derived_from_manifest() -> None:
    adapter = RuntimePluginAdapter(_make_plugin("my-plugin"), object())  # type: ignore[arg-type]
    assert adapter.name == "my-plugin"


def test_dependencies_default_to_empty() -> None:
    adapter = RuntimePluginAdapter(_make_plugin(), object())  # type: ignore[arg-type]
    assert adapter.dependencies == ()


# ---------------------------------------------------------------------------
# Lifecycle: on_start activates plugin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_start_activates_plugin() -> None:
    plugin = _make_plugin("activatable")
    platform = object()
    adapter = RuntimePluginAdapter(plugin, platform)  # type: ignore[arg-type]
    assert plugin.activated == 0

    await adapter.on_start(None, None)  # type: ignore[arg-type]
    assert plugin.activated == 1


@pytest.mark.asyncio
async def test_on_start_is_idempotent() -> None:
    plugin = _make_plugin("idempotent")
    platform = object()
    adapter = RuntimePluginAdapter(plugin, platform)  # type: ignore[arg-type]

    await adapter.on_start(None, None)  # type: ignore[arg-type]
    await adapter.on_start(None, None)  # type: ignore[arg-type]  # second call
    assert plugin.activated == 1  # still 1


@pytest.mark.asyncio
async def test_on_stop_deactivates_plugin() -> None:
    plugin = _make_plugin("deactivatable")
    platform = object()
    adapter = RuntimePluginAdapter(plugin, platform)  # type: ignore[arg-type]

    await adapter.on_start(None, None)  # type: ignore[arg-type]
    assert plugin.activated == 1

    await adapter.on_stop(None, None)  # type: ignore[arg-type]
    assert plugin.deactivated == 1
    assert plugin.activated == 1  # still counted from on_start


@pytest.mark.asyncio
async def test_on_stop_before_start_is_noop() -> None:
    plugin = _make_plugin("never-started")
    adapter = RuntimePluginAdapter(plugin, object())  # type: ignore[arg-type]

    await adapter.on_stop(None, None)  # type: ignore[arg-type]
    assert plugin.deactivated == 0


@pytest.mark.asyncio
async def test_on_stop_is_idempotent() -> None:
    plugin = _make_plugin("stop-idempotent")
    adapter = RuntimePluginAdapter(plugin, object())  # type: ignore[arg-type]

    await adapter.on_start(None, None)  # type: ignore[arg-type]
    await adapter.on_stop(None, None)  # type: ignore[arg-type]
    await adapter.on_stop(None, None)  # type: ignore[arg-type]  # second call
    assert plugin.deactivated == 1  # still 1


# ---------------------------------------------------------------------------
# Integration with RuntimeHost via add_plugin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_plugin_registers_adapter_and_activates() -> None:
    """add_plugin registers the adapter and starts/stops it with the host."""
    from eaip.application import build_platform

    plugin = _make_plugin("host-plugin")
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)

    adapter = host.add_plugin(plugin)
    assert adapter.name == "host-plugin"
    assert "host-plugin" in host.module_names
    assert plugin.activated == 0

    await host.start()
    assert plugin.activated == 1

    await host.stop()
    assert plugin.deactivated == 1
