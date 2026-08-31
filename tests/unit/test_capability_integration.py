"""Tests for :mod:`eaip.runtime.capability_integration`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.capabilities.registry import CapabilityRegistry
from eaip.runtime.capability_integration import CapabilityRuntimeModule

if TYPE_CHECKING:
    pass


class _MockPlatform:
    def __init__(self) -> None:
        self._health_checks: dict[str, Any] = {}

    @property
    def health(self) -> Any:
        class _Health:
            def __init__(self, checks: dict[str, Any]) -> None:
                self._checks = checks

            def register(self, check: Any) -> None:
                self._checks[check.name] = check

        return _Health(self._health_checks)

    @property
    def plugin_loader(self) -> Any:
        class _Loader:
            def all(self) -> list[Any]:
                return []

        return _Loader()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


def test_startup_duration_starts_zero() -> None:
    module = CapabilityRuntimeModule(CapabilityRegistry())
    assert module.startup_duration == 0.0


def test_stop_disables_enabled() -> None:
    registry = CapabilityRegistry()
    c = Capability(name="test", title="Test", version="1.0.0")
    registry.register(c)
    registry.enable("test")

    import asyncio

    module = CapabilityRuntimeModule(registry)
    kernel = _MockKernel()
    asyncio.run(module.stop(kernel))

    assert registry.get("test").status is CapabilityStatus.DISABLED
