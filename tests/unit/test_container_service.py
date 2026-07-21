"""Tests for :mod:`eaip.container.orchestrator`."""

from __future__ import annotations

import pytest

from eaip.container.exceptions import ContainerNotFoundError
from eaip.container.models import Container, ContainerConfig, ContainerDeployment, ContainerStatus
from eaip.container.orchestrator import ContainerOrchestrator


class TestContainerOrchestrator:
    @pytest.fixture
    def orchestrator(self) -> ContainerOrchestrator:
        return ContainerOrchestrator()

    @pytest.fixture
    def container(self) -> Container:
        return Container(id="c1", name="web-app", image="nginx:latest")

    @pytest.fixture
    def deployment(self) -> ContainerDeployment:
        return ContainerDeployment(id="d1", container_id="c1", replicas=3)

    class TestDeploy:
        async def test_deploy(
            self,
            orchestrator: ContainerOrchestrator,
            container: Container,
            deployment: ContainerDeployment,
        ) -> None:
            result = await orchestrator.deploy(container, deployment)
            assert result.id == "c1"
            assert result.status == ContainerStatus.PENDING

        async def test_list_containers(
            self,
            orchestrator: ContainerOrchestrator,
            container: Container,
            deployment: ContainerDeployment,
        ) -> None:
            await orchestrator.deploy(container, deployment)
            containers = await orchestrator.list_containers()
            assert len(containers) == 1

    class TestScale:
        async def test_scale(
            self,
            orchestrator: ContainerOrchestrator,
            container: Container,
            deployment: ContainerDeployment,
        ) -> None:
            await orchestrator.deploy(container, deployment)
            result = await orchestrator.scale("c1", 5)
            assert result.replicas == 5

        async def test_scale_not_found(self, orchestrator: ContainerOrchestrator) -> None:
            with pytest.raises(ContainerNotFoundError):
                await orchestrator.scale("nonexistent", 3)

    class TestStop:
        async def test_stop(
            self,
            orchestrator: ContainerOrchestrator,
            container: Container,
            deployment: ContainerDeployment,
        ) -> None:
            await orchestrator.deploy(container, deployment)
            await orchestrator.stop("c1")
            c = await orchestrator.get_container("c1")
            assert c.status == ContainerStatus.STOPPED

        async def test_stop_not_found(self, orchestrator: ContainerOrchestrator) -> None:
            with pytest.raises(ContainerNotFoundError):
                await orchestrator.stop("nonexistent")

    class TestGetContainer:
        async def test_get(
            self,
            orchestrator: ContainerOrchestrator,
            container: Container,
            deployment: ContainerDeployment,
        ) -> None:
            await orchestrator.deploy(container, deployment)
            c = await orchestrator.get_container("c1")
            assert c.name == "web-app"

        async def test_not_found(self, orchestrator: ContainerOrchestrator) -> None:
            with pytest.raises(ContainerNotFoundError):
                await orchestrator.get_container("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            o = ContainerOrchestrator()
            assert o.config.default_replicas == 1
            assert o.config.max_replicas == 10

        def test_custom_config(self) -> None:
            config = ContainerConfig(default_replicas=2, max_replicas=20)
            o = ContainerOrchestrator(config=config)
            assert o.config.default_replicas == 2
            assert o.config.max_replicas == 20
