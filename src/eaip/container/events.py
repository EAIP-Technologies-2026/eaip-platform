"""Domain events for the container orchestrator."""

from __future__ import annotations

from typing import ClassVar

from eaip.container.models import ContainerStatus
from eaip.events.event import DomainEvent


class ContainerDeployed(DomainEvent):
    event_type: ClassVar[str] = "eaip.container.deployed"
    container_id: str
    deployment_id: str
    replicas: int


class ContainerScaled(DomainEvent):
    event_type: ClassVar[str] = "eaip.container.scaled"
    container_id: str
    deployment_id: str
    previous_replicas: int
    new_replicas: int


class ContainerStopped(DomainEvent):
    event_type: ClassVar[str] = "eaip.container.stopped"
    container_id: str
    deployment_id: str


class ContainerHealthChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.container.health_changed"
    container_id: str
    previous_status: ContainerStatus
    new_status: ContainerStatus


__all__ = [
    "ContainerDeployed",
    "ContainerHealthChanged",
    "ContainerScaled",
    "ContainerStopped",
]
