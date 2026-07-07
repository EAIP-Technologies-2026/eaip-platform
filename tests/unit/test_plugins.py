"""Tests for :mod:`eaip.plugins`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from eaip.exceptions.domain import PluginContractViolationError, PluginError
from eaip.plugins import Plugin, PluginManifest, PluginRegistry
from eaip.plugins.loader import CURRENT_CONTRACT_VERSION, PluginLoader

if TYPE_CHECKING:  # pragma: no cover
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


def _plug(name: str = "demo", contract: str = CURRENT_CONTRACT_VERSION) -> _DummyPlugin:
    return _DummyPlugin(
        manifest=PluginManifest(name=name, version="0.1.0", contract_version=contract)
    )


def test_install_and_uninstall() -> None:
    reg = PluginRegistry()
    loader = PluginLoader(reg)
    p = _plug()
    loader.install(p)
    assert reg.has(p.manifest.name)
    loader.uninstall(p.manifest.name)
    assert not reg.has(p.manifest.name)


def test_contract_major_mismatch_rejected() -> None:
    reg = PluginRegistry()
    loader = PluginLoader(reg)
    bad_major = str(int(CURRENT_CONTRACT_VERSION.split(".", 1)[0]) + 99) + ".0.0"
    with pytest.raises(PluginContractViolationError):
        loader.install(_plug("bad", contract=bad_major))


@pytest.mark.asyncio
async def test_activate_and_deactivate_lifecycle() -> None:
    reg = PluginRegistry()
    loader = PluginLoader(reg)
    p = _plug("alpha")
    loader.install(p)

    # Use a placeholder; loader only forwards `platform` to plugin callbacks.
    sentinel = object()
    await loader.activate("alpha", sentinel)  # type: ignore[arg-type]
    await loader.activate("alpha", sentinel)  # type: ignore[arg-type]  # idempotent
    assert p.activated == 1
    assert "alpha" in loader.activated

    await loader.deactivate("alpha", sentinel)  # type: ignore[arg-type]
    await loader.deactivate("alpha", sentinel)  # type: ignore[arg-type]  # idempotent
    assert p.deactivated == 1


def test_uninstall_active_plugin_rejected() -> None:
    reg = PluginRegistry()
    loader = PluginLoader(reg)
    p = _plug()
    loader.install(p)
    loader._activated.add(p.manifest.name)
    with pytest.raises(PluginError):
        loader.uninstall(p.manifest.name)


def test_protocol_isinstance_check() -> None:
    p = _plug()
    assert isinstance(p, Plugin)
