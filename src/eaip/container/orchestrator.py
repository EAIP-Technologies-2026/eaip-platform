"""ContainerOrchestrator — central service for managing container lifecycles."""

from __future__ import annotations

from eaip.container.events import (
    ContainerDeployed,
    ContainerScaled,
    ContainerStopped,
)
from eaip.container.exceptions import ContainerNotFoundError
from eaip.container.models import (
    Container,
    ContainerConfig,
    ContainerDeployment,
    ContainerStatus,
)
from eaip.logging.context import get_logger


class ContainerOrchestrator:
    def __init__(self, config: ContainerConfig | None = None) -> None:
        self._config = config or ContainerConfig()
        self._containers: dict[str, Container] = {}
        self._deployments: dict[str, ContainerDeployment] = {}
        self._log = get_logger("eaip.container.orchestrator")

    @property
    def config(self) -> ContainerConfig:
        return self._config

    async def deploy(self, container: Container, deployment: ContainerDeployment) -> Container:
        self._containers[container.id] = container
        self._deployments[deployment.id] = deployment
        event = ContainerDeployed(
            container_id=container.id,
            deployment_id=deployment.id,
            replicas=deployment.replicas,
        )
        self._log.info("container.deployed", container_id=container.id)
        return container

    async def scale(self, container_id: str, replicas: int) -> ContainerDeployment:
        deployment = self._get_deployment(container_id)
        previous = deployment.replicas
        updated = ContainerDeployment(
            id=deployment.id,
            container_id=deployment.container_id,
            replicas=replicas,
            strategy=deployment.strategy,
            exposed_ports=deployment.exposed_ports,
            env_vars=deployment.env_vars,
        )
        self._deployments[deployment.id] = updated
        event = ContainerScaled(
            container_id=container_id,
            deployment_id=deployment.id,
            previous_replicas=previous,
            new_replicas=replicas,
        )
        self._log.info("container.scaled", container_id=container_id, replicas=replicas)
        return updated

    async def stop(self, container_id: str) -> None:
        container = self._get_container(container_id)
        updated = Container(
            id=container.id,
            name=container.name,
            image=container.image,
            status=ContainerStatus.STOPPED,
            port=container.port,
            resources=container.resources,
            labels=container.labels,
            created_at=container.created_at,
        )
        self._containers[container_id] = updated
        event = ContainerStopped(
            container_id=container_id,
            deployment_id="",
        )
        self._log.info("container.stopped", container_id=container_id)

    async def get_container(self, container_id: str) -> Container:
        return self._get_container(container_id)

    async def list_containers(self) -> list[Container]:
        return list(self._containers.values())

    async def get_deployment(self, container_id: str) -> ContainerDeployment:
        return self._get_deployment(container_id)

    def _get_container(self, container_id: str) -> Container:
        container = self._containers.get(container_id)
        if container is None:
            raise ContainerNotFoundError(f"Container '{container_id}' not found")
        return container

    def _get_deployment(self, container_id: str) -> ContainerDeployment:
        for d in self._deployments.values():
            if d.container_id == container_id:
                return d
        raise ContainerNotFoundError(f"No deployment found for container '{container_id}'")
