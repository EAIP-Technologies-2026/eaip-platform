"""Tests for :mod:`eaip.container.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.container.events import (
    ContainerDeployed,
    ContainerHealthChanged,
    ContainerScaled,
    ContainerStopped,
)
from eaip.container.models import ContainerStatus
from eaip.events.event import DomainEvent


class TestContainerDeployed:
    def test_event_type(self) -> None:
        event = ContainerDeployed(container_id="c1", deployment_id="d1", replicas=3)
        assert event.event_type == "eaip.container.deployed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ContainerDeployed(container_id="c1", deployment_id="d1", replicas=3)
        assert event.container_id == "c1"
        assert event.deployment_id == "d1"
        assert event.replicas == 3


class TestContainerScaled:
    def test_event_type(self) -> None:
        event = ContainerScaled(
            container_id="c1", deployment_id="d1", previous_replicas=2, new_replicas=5
        )
        assert event.event_type == "eaip.container.scaled"

    def test_fields(self) -> None:
        event = ContainerScaled(
            container_id="c1", deployment_id="d1", previous_replicas=2, new_replicas=5
        )
        assert event.previous_replicas == 2
        assert event.new_replicas == 5


class TestContainerStopped:
    def test_event_type(self) -> None:
        event = ContainerStopped(container_id="c1", deployment_id="d1")
        assert event.event_type == "eaip.container.stopped"


class TestContainerHealthChanged:
    def test_event_type(self) -> None:
        event = ContainerHealthChanged(
            container_id="c1",
            previous_status=ContainerStatus.RUNNING,
            new_status=ContainerStatus.FAILED,
        )
        assert event.event_type == "eaip.container.health_changed"

    def test_fields(self) -> None:
        event = ContainerHealthChanged(
            container_id="c1",
            previous_status=ContainerStatus.RUNNING,
            new_status=ContainerStatus.FAILED,
        )
        assert event.previous_status == ContainerStatus.RUNNING
        assert event.new_status == ContainerStatus.FAILED


class TestEventImmutability:
    def test_frozen(self) -> None:
        event = ContainerDeployed(container_id="c1", deployment_id="d1", replicas=3)
        with pytest.raises(ValidationError):
            event.container_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        event = ContainerDeployed(container_id="c1", deployment_id="d1", replicas=3)
        assert event.occurred_at is not None
