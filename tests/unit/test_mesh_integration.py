"""Tests for :mod:`eaip.mesh.integration`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.mesh.integration import MeshRuntimeModule


class TestMeshRuntimeModule:
    def test_default_initialization(self) -> None:
        module = MeshRuntimeModule()
        assert module.name == "mesh"
        assert module.registry is not None
        assert module.router is not None
        assert module.load_balancer is not None
        assert module.circuit_breaker is not None

    def test_properties(self) -> None:
        module = MeshRuntimeModule()
        assert module.registry is module._registry
        assert module.router is module._router
        assert module.load_balancer is module._load_balancer
        assert module.circuit_breaker is module._circuit_breaker

    @pytest.mark.asyncio
    async def test_start_registers_capability_and_health(self) -> None:
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        module = MeshRuntimeModule()
        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()
        capability = kernel.platform.capabilities.register.call_args[0][0]
        assert capability.name == "eaip.mesh"

    @pytest.mark.asyncio
    async def test_start_logs(self) -> None:
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        module = MeshRuntimeModule()
        await module.start(kernel)

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        kernel = MagicMock()
        module = MeshRuntimeModule()
        await module.stop(kernel)
        # No-op, just verifies it doesn't error

    @pytest.mark.asyncio
    async def test_register_and_route_lifecycle(self) -> None:
        from eaip.mesh.models import ServiceInstance, ServiceRoute, ServiceStatus

        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        module = MeshRuntimeModule()
        await module.start(kernel)

        inst = ServiceInstance(
            id="svc-1",
            name="test-svc",
            host="10.0.0.1",
            port=8080,
            status=ServiceStatus.UP,
        )
        module.registry.register(inst)

        route = ServiceRoute(
            id="r-1",
            name="test-route",
            source_service="gateway",
            destination_service="test-svc",
        )
        module.router.register_route(route)

        result = await module.router.route_request(
            source="gateway",
            destination="test-svc",
        )
        assert result.id == "svc-1"
