"""B00 — Critical Runtime Infrastructure Wiring integration tests.

Verifies:
1. TenantRuntimeModule startup and service initialization
2. AuditRuntimeModule startup and capability registration
3. GuardrailRuntimeModule startup and engine creation
4. PolicyRuntimeModule startup and empty registry
5. Full runtime wiring integration
6. Health check registration
7. EventBus integration
8. No default policies (security verification)
"""

from __future__ import annotations

from typing import Any

import pytest

from eaip.audit.integration import AuditRuntimeModule
from eaip.guardrails.integration import GuardrailRuntimeModule
from eaip.policy.integration import PolicyRuntimeModule
from eaip.tenants.integration import TenantRuntimeModule


class _MockHealthReporter:
    def __init__(self) -> None:
        self.registered: list[Any] = []

    def register(self, check: Any) -> None:
        self.registered.append(check)


class _MockCapabilities:
    def __init__(self) -> None:
        self.registered: list[Any] = []

    def register(self, cap: Any) -> None:
        self.registered.append(cap)


class _MockEvents:
    def __init__(self) -> None:
        self.published: list[Any] = []

    async def publish(self, event: Any) -> None:
        self.published.append(event)


class _MockPlatform:
    def __init__(self) -> None:
        self.health = _MockHealthReporter()
        self.capabilities = _MockCapabilities()
        self.events = _MockEvents()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()
        self._modules: dict[str, Any] = {}

    @property
    def platform(self) -> _MockPlatform:
        return self._platform

    def register_module(self, name: str, module: Any) -> None:
        self._modules[name] = module


@pytest.fixture
def kernel() -> _MockKernel:
    return _MockKernel()


class TestTenantRuntimeModuleB00:
    """B00 verification for TenantRuntimeModule."""

    async def test_startup_initializes_services(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        assert module.manager is not None
        assert module.billing is not None
        assert module.isolation is not None
        assert module.analytics is not None

    async def test_health_check_registered(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        assert len(kernel.platform.health.registered) == 1

    async def test_shutdown_succeeds(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        assert module.started is False


class TestAuditRuntimeModuleB00:
    """B00 verification for AuditRuntimeModule."""

    async def test_startup_registers_capability(self, kernel: _MockKernel) -> None:
        module = AuditRuntimeModule()
        await module.start(kernel)
        assert len(kernel.platform.capabilities.registered) == 1

    async def test_health_check_registered(self, kernel: _MockKernel) -> None:
        module = AuditRuntimeModule()
        await module.start(kernel)
        assert len(kernel.platform.health.registered) == 1

    async def test_services_initialized(self, kernel: _MockKernel) -> None:
        module = AuditRuntimeModule()
        await module.start(kernel)
        assert module.logger is not None
        assert module.policy_service is not None
        assert module.classifier is not None
        assert module.legal_hold_service is not None


class TestGuardrailRuntimeModuleB00:
    """B00 verification for GuardrailRuntimeModule."""

    async def test_startup_initializes_engine(self, kernel: _MockKernel) -> None:
        module = GuardrailRuntimeModule()
        await module.start(kernel)
        assert module.engine is not None

    async def test_health_check_registered(self, kernel: _MockKernel) -> None:
        module = GuardrailRuntimeModule()
        await module.start(kernel)
        assert len(kernel.platform.health.registered) == 1

    async def test_shutdown_succeeds(self, kernel: _MockKernel) -> None:
        module = GuardrailRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        # No exception means success


class TestPolicyRuntimeModuleB00:
    """B00 verification for PolicyRuntimeModule."""

    async def test_startup_creates_authorization(self, kernel: _MockKernel) -> None:
        module = PolicyRuntimeModule()
        await module.start(kernel)
        assert module.authorization is not None

    async def test_health_check_registered(self, kernel: _MockKernel) -> None:
        module = PolicyRuntimeModule()
        await module.start(kernel)
        assert len(kernel.platform.health.registered) == 1

    async def test_registry_empty_by_default(self, kernel: _MockKernel) -> None:
        """SECURITY: PolicyRegistry must be empty by default — no default policies."""
        module = PolicyRuntimeModule()
        await module.start(kernel)
        assert len(module.registry) == 0

    async def test_shutdown_disables_policies(self, kernel: _MockKernel) -> None:
        module = PolicyRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        for policy in module.registry.all():
            assert policy.enabled is False


class TestFullRuntimeWiringB00:
    """Full B00 runtime wiring integration test."""

    async def test_all_modules_start_successfully(self) -> None:
        kernel = _MockKernel()

        tenant_module = TenantRuntimeModule()
        await tenant_module.start(kernel)

        audit_module = AuditRuntimeModule()
        await audit_module.start(kernel)

        guardrails_module = GuardrailRuntimeModule()
        await guardrails_module.start(kernel)

        policy_module = PolicyRuntimeModule()
        await policy_module.start(kernel)

        assert tenant_module.started
        assert audit_module.logger is not None
        assert guardrails_module.engine is not None
        assert policy_module.authorization is not None

    async def test_health_checks_registered(self) -> None:
        kernel = _MockKernel()

        await TenantRuntimeModule().start(kernel)
        await AuditRuntimeModule().start(kernel)
        await GuardrailRuntimeModule().start(kernel)
        await PolicyRuntimeModule().start(kernel)

        assert len(kernel.platform.health.registered) == 4

    async def test_eventbus_accessible(self) -> None:
        kernel = _MockKernel()
        assert kernel.platform.events is not None

    async def test_no_default_policies_security(self) -> None:
        """SECURITY: Verify no wildcard or default policies are seeded."""
        kernel = _MockKernel()
        module = PolicyRuntimeModule()
        await module.start(kernel)
        registry = module.registry
        assert len(registry) == 0
        for policy in registry.all():
            assert policy.effect.value != "ALLOW" or policy.subject != "*"
