"""Tests for :mod:`eaip.admin.manager`."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.admin.manager import RuntimeManager
from eaip.admin.models import RuntimeSnapshot
from eaip.events.bus import EventBus


class _MockHealthReport:
    def __init__(self, status: Any = None) -> None:
        self.status = status or _MockStatus("healthy")
        self.component = "test"
        self.children = ()
        self.message = ""
        self.details = {}


class _MockStatus:
    def __init__(self, value: str) -> None:
        self.value = value


class _MockCapability:
    def __init__(self, name: str, status: str = "enabled") -> None:
        self.name = name
        self.status = status


class _MockCapabilityRegistry:
    def __init__(self) -> None:
        self._caps: dict[str, _MockCapability] = {}

    def register(self, cap: _MockCapability) -> None:
        self._caps[cap.name] = cap

    def all(self) -> list[_MockCapability]:
        return list(self._caps.values())

    def list(self) -> list[_MockCapability]:
        return list(self._caps.values())

    def enable(self, name: str) -> None:
        if name not in self._caps:
            raise LookupError(name)
        self._caps[name].status = "enabled"

    def disable(self, name: str) -> None:
        if name not in self._caps:
            raise LookupError(name)
        self._caps[name].status = "disabled"

    def get(self, name: str) -> _MockCapability | None:
        return self._caps.get(name)


class _MockPluginLoader:
    async def deactivate(self, name: str, platform: Any) -> None:
        pass

    async def activate(self, name: str, platform: Any) -> None:
        pass


class _MockHealth:
    async def report(self) -> _MockHealthReport:
        return _MockHealthReport()

    def register(self, check: Any) -> None:
        pass


class _MockPlatform:
    def __init__(self) -> None:
        self.capabilities = _MockCapabilityRegistry()
        self.health = _MockHealth()
        self.plugin_loader = _MockPluginLoader()
        self._settings = object()

    @property
    def settings(self) -> Any:
        return self._settings


class _MockKernel:
    def __init__(self) -> None:
        self._modules: dict[str, object] = {
            "admin": object(),
            "events": object(),
        }
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


@pytest.fixture
def kernel() -> _MockKernel:
    return _MockKernel()


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def manager(kernel: _MockKernel) -> RuntimeManager:
    return RuntimeManager(kernel)


@pytest.fixture
def manager_with_bus(kernel: _MockKernel, event_bus: EventBus) -> RuntimeManager:
    return RuntimeManager(kernel, event_bus)


class TestRuntimeManager:
    async def test_get_snapshot(self, manager: RuntimeManager) -> None:
        snap = await manager.get_snapshot()
        assert isinstance(snap, RuntimeSnapshot)
        assert snap.health_status == "healthy"
        assert "admin" in snap.active_modules

    async def test_get_snapshot_active_capabilities(self, manager: RuntimeManager) -> None:
        platform = manager.platform
        platform.capabilities.register(_MockCapability("logging"))
        platform.capabilities.register(_MockCapability("metrics", "disabled"))
        snap = await manager.get_snapshot()
        assert "logging" in snap.active_capabilities
        assert "metrics" not in snap.active_capabilities

    async def test_toggle_capability_enable(self, manager: RuntimeManager) -> None:
        platform = manager.platform
        platform.capabilities.register(_MockCapability("test-cap", "disabled"))
        result = await manager.toggle_capability("test-cap", True)
        assert result is True
        assert platform.capabilities.get("test-cap").status == "enabled"

    async def test_toggle_capability_disable(self, manager: RuntimeManager) -> None:
        platform = manager.platform
        platform.capabilities.register(_MockCapability("test-cap", "enabled"))
        result = await manager.toggle_capability("test-cap", False)
        assert result is True
        assert platform.capabilities.get("test-cap").status == "disabled"

    async def test_toggle_nonexistent_capability_raises(self, manager: RuntimeManager) -> None:
        with pytest.raises(ValueError, match="not found"):
            await manager.toggle_capability("does-not-exist", True)

    async def test_reload_plugin(self, manager: RuntimeManager) -> None:
        result = await manager.reload_plugin("test-plugin")
        assert result is True

    async def test_reload_plugin_failure(self, manager: RuntimeManager) -> None:
        class _FailingLoader:
            async def deactivate(self, name: str, platform: Any) -> None:
                raise RuntimeError("fail")

            async def activate(self, name: str, platform: Any) -> None:
                raise RuntimeError("fail")

        manager.platform.plugin_loader = _FailingLoader()
        result = await manager.reload_plugin("broken")
        assert result is False

    async def test_get_config(self, manager: RuntimeManager) -> None:
        config = await manager.get_config()
        assert config is manager.platform.settings

    def test_list_active_modules(self, manager: RuntimeManager) -> None:
        modules = manager.list_active_modules()
        assert "admin" in modules
        assert "events" in modules

    def test_list_active_capabilities(self, manager: RuntimeManager) -> None:
        platform = manager.platform
        platform.capabilities.register(_MockCapability("foo", "enabled"))
        platform.capabilities.register(_MockCapability("bar", "disabled"))
        active = manager.list_active_capabilities()
        assert "foo" in active
        assert "bar" not in active

    def test_get_health_summary(self, manager: RuntimeManager) -> None:
        summary = manager.get_health_summary()
        assert "status" in summary
        assert "summary" in summary

    async def test_toggle_with_event_bus(self, manager_with_bus: RuntimeManager) -> None:
        platform = manager_with_bus.platform
        platform.capabilities.register(_MockCapability("evt-cap", "disabled"))
        result = await manager_with_bus.toggle_capability("evt-cap", True)
        assert result is True
