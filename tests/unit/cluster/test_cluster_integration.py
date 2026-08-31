"""Tests for ClusterRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.cluster.coordinator import ClusterCoordinator
from eaip.cluster.health import ClusterHealthCheck
from eaip.cluster.integration import ClusterRuntimeModule
from eaip.cluster.models import ClusterConfig


class TestClusterRuntimeModule:
    def test_default_construction(self) -> None:
        module = ClusterRuntimeModule()
        assert module.name == "cluster"
        assert isinstance(module.coordinator, ClusterCoordinator)

    def test_custom_construction(self) -> None:
        config = ClusterConfig(cluster_name="custom")
        coord = ClusterCoordinator(config=config)
        module = ClusterRuntimeModule(config=config, coordinator=coord)
        assert module.coordinator.config.cluster_name == "custom"

    async def test_start_registers_capability(self) -> None:
        module = ClusterRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    async def test_start_registers_health_check(
        self,
    ) -> None:
        module = ClusterRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.health.register.call_args
        registered = call_args[0][0]
        assert isinstance(registered, ClusterHealthCheck)

    async def test_stop(self) -> None:
        module = ClusterRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)

    async def test_start_with_capability_tags(
        self,
    ) -> None:
        module = ClusterRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.capabilities.register.call_args
        capability = call_args[0][0]
        assert capability.name == "eaip.cluster"
        assert "cluster" in capability.tags
        assert "coordination" in capability.tags
        assert "ha" in capability.tags
