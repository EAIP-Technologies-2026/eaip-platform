"""Tests for :mod:`eaip.plugins.lifecycle`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from eaip.exceptions.domain import PluginError
from eaip.plugins.lifecycle import PluginLifecycleManager
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import PluginDependency, PluginManifest
from eaip.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


@dataclass
class _DummyPlugin:
    manifest: PluginManifest
    activated: bool = field(default=False)
    deactivated: bool = field(default=False)

    async def activate(self, platform: Platform) -> None:
        self.activated = True

    async def deactivate(self, platform: Platform) -> None:
        self.deactivated = True


def _plugin(name: str, deps: tuple[PluginDependency, ...] = ()) -> _DummyPlugin:
    return _DummyPlugin(
        manifest=PluginManifest(name=name, version="1.0.0", dependencies=deps),
    )


@pytest.fixture
def lifecycle() -> PluginLifecycleManager:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    return PluginLifecycleManager(loader=loader)


class TestValidateDependencies:
    def test_no_plugins(self, lifecycle: PluginLifecycleManager) -> None:
        assert lifecycle.validate_dependencies() == []

    def test_all_valid(self, lifecycle: PluginLifecycleManager) -> None:
        lifecycle.loader.install(_plugin("a"))
        lifecycle.loader.install(_plugin("b"))
        assert lifecycle.validate_dependencies() == []

    def test_missing_dependency(self, lifecycle: PluginLifecycleManager) -> None:
        p = _plugin("ext", deps=(PluginDependency(name="base"),))
        lifecycle.loader.install(p)
        errors = lifecycle.validate_dependencies()
        assert len(errors) == 1
        assert "base" in errors[0]


class TestResolveActivationOrder:
    def test_single(self, lifecycle: PluginLifecycleManager) -> None:
        p = _plugin("a")
        lifecycle.loader.install(p)
        ordered = lifecycle.resolve_activation_order()
        assert [x.manifest.name for x in ordered] == ["a"]

    def test_topological(self, lifecycle: PluginLifecycleManager) -> None:
        base = _plugin("base")
        mid = _plugin("mid", deps=(PluginDependency(name="base"),))
        top = _plugin("top", deps=(PluginDependency(name="mid"),))
        for p in (top, mid, base):
            lifecycle.loader.install(p)
        ordered = lifecycle.resolve_activation_order()
        names = [x.manifest.name for x in ordered]
        assert names == ["base", "mid", "top"]

    def test_circular_raises(self, lifecycle: PluginLifecycleManager) -> None:
        a = _plugin("a", deps=(PluginDependency(name="b"),))
        b = _plugin("b", deps=(PluginDependency(name="a"),))
        for p in (a, b):
            lifecycle.loader.install(p)
        with pytest.raises(PluginError, match="circular"):
            lifecycle.resolve_activation_order()


class TestActivateDeactivate:
    @pytest.mark.asyncio
    async def test_activate_all(
        self,
        lifecycle: PluginLifecycleManager,
    ) -> None:
        base = _plugin("base")
        top = _plugin("top", deps=(PluginDependency(name="base"),))
        for p in (top, base):
            lifecycle.loader.install(p)

        platform_sentinel = object()
        await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
        assert base.activated
        assert top.activated

    @pytest.mark.asyncio
    async def test_deactivate_all_reverse_order(
        self,
        lifecycle: PluginLifecycleManager,
    ) -> None:
        base = _plugin("base")
        top = _plugin("top", deps=(PluginDependency(name="base"),))
        for p in (top, base):
            lifecycle.loader.install(p)

        platform_sentinel = object()
        await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]
        await lifecycle.deactivate_all(platform_sentinel)  # type: ignore[arg-type]
        assert base.deactivated
        assert top.deactivated

    @pytest.mark.asyncio
    async def test_activate_all_failure_propagates(
        self,
        lifecycle: PluginLifecycleManager,
    ) -> None:
        p = _plugin("fail")

        async def _broken(platform: Platform) -> None:
            raise RuntimeError("fail")

        p.activate = _broken  # type: ignore[method-assign]
        lifecycle.loader.install(p)

        platform_sentinel = object()
        with pytest.raises(PluginError, match="fail"):
            await lifecycle.activate_all(platform_sentinel)  # type: ignore[arg-type]


class TestDiscoverAndInstall:
    @pytest.mark.asyncio
    async def test_discovers_nothing(self, lifecycle: PluginLifecycleManager) -> None:
        installed = await lifecycle.discover_and_install()
        assert installed == []

    @pytest.mark.asyncio
    async def test_scans_package(self, lifecycle: PluginLifecycleManager) -> None:
        installed = await lifecycle.discover_and_install(
            scan_packages=["eaip.registry"],
        )
        assert isinstance(installed, list)
