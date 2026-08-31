"""Tests for SessionRuntimeModule integration."""

from __future__ import annotations

import asyncio

from eaip.session.context_manager import EnterpriseContextManager
from eaip.session.integration import SessionRuntimeModule, create_session_integration
from eaip.session.lifecycle import SessionLifecycleManager
from eaip.session.manager import SessionManager
from eaip.session.serialization import SessionSerializer


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict = {}

    def register(self, check: object) -> None:
        self._checks[check.name] = check

    def registered(self) -> list[str]:
        return sorted(self._checks)


class _MockCapabilities:
    def __init__(self) -> None:
        self._caps: list = []

    def register(self, cap: object) -> None:
        self._caps.append(cap)


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()
        self._capabilities = _MockCapabilities()

    @property
    def health(self) -> _MockHealth:
        return self._health

    @property
    def capabilities(self) -> _MockCapabilities:
        return self._capabilities


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestSessionRuntimeModule:
    def test_start_stop_lifecycle(self) -> None:
        module = SessionRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        assert module.manager is not None
        assert module.context_manager is not None
        assert module.serializer is not None
        asyncio.run(module.stop(kernel))

    def test_health_check_registered(self) -> None:
        module = SessionRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        registered = kernel.platform.health.registered()
        assert "session" in registered
        asyncio.run(module.stop(kernel))

    def test_capability_registered(self) -> None:
        module = SessionRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform._capabilities._caps) == 1
        cap = kernel.platform._capabilities._caps[0]
        assert cap.name == "session:engine"
        asyncio.run(module.stop(kernel))

    def test_constructor_with_manager(self) -> None:
        mgr = SessionManager()
        module = SessionRuntimeModule(manager=mgr)
        assert module.manager is mgr

    def test_constructor_with_context_manager(self) -> None:
        cm = EnterpriseContextManager()
        module = SessionRuntimeModule(context_manager=cm)
        assert module.context_manager is cm

    def test_constructor_with_lifecycle_manager(self) -> None:
        mgr = SessionManager()
        lcm = SessionLifecycleManager(mgr)
        module = SessionRuntimeModule(lifecycle_manager=lcm)
        assert module.lifecycle_manager is lcm

    def test_constructor_with_serializer(self) -> None:
        ser = SessionSerializer()
        module = SessionRuntimeModule(serializer=ser)
        assert module.serializer is ser

    def test_create_session_integration(self) -> None:
        module = create_session_integration()
        assert isinstance(module, SessionRuntimeModule)

    def test_create_session_integration_with_components(self) -> None:
        mgr = SessionManager()
        cm = EnterpriseContextManager()
        lcm = SessionLifecycleManager(mgr)
        ser = SessionSerializer()
        module = create_session_integration(
            manager=mgr,
            context_manager=cm,
            lifecycle_manager=lcm,
            serializer=ser,
        )
        assert module.manager is mgr
        assert module.context_manager is cm
        assert module.lifecycle_manager is lcm
        assert module.serializer is ser
