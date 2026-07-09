from __future__ import annotations

import asyncio

from eaip.health.checks import HealthStatus
from eaip.policy.engine import PolicyEngine
from eaip.policy.integration import PolicyRuntimeModule
from eaip.policy.models import Policy, PolicyDecision, PolicyEffect, PolicyRule
from eaip.policy.registry import PolicyRegistry


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict = {}

    def register(self, check) -> None:
        self._checks[check.name] = check

    def registered(self) -> list[str]:
        return sorted(self._checks)


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()

    @property
    def health(self):
        return self._health

    @property
    def events(self):
        return None


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self):
        return self._platform


class TestPolicyRuntimeModule:
    def test_start_stop_lifecycle(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        module = PolicyRuntimeModule(registry=registry, engine=PolicyEngine())
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        assert module.engine is not None
        assert module.registry is not None
        assert "policy" in kernel.platform.health.registered()
        asyncio.run(module.stop(kernel))

    def test_authorization_available_after_start(self) -> None:
        module = PolicyRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        auth = module.authorization
        assert auth is not None

    def test_authorization_raises_before_start(self) -> None:
        module = PolicyRuntimeModule()
        try:
            _ = module.authorization
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass

    def test_stop_disables_policies(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        module = PolicyRuntimeModule(registry=registry)
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        asyncio.run(module.stop(kernel))
        for p in registry.all():
            assert p.enabled is False

    def test_health_check_is_healthy(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(id="p1", name="p1"))
        module = PolicyRuntimeModule(registry=registry)
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        report = asyncio.run(kernel.platform.health._checks["policy"].check())
        assert report.status is HealthStatus.HEALTHY
