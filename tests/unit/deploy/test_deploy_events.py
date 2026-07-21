"""Tests for deploy domain events."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.deploy.events import (
    DeployEvent,
    DeploymentCompleted,
    DeploymentFailed,
    DeploymentRolledBack,
    DeploymentStarted,
    EnvironmentUpdated,
    ReleaseCreated,
    ReleasePromoted,
)


class TestReleaseCreated:
    def test_defaults(self) -> None:
        event = ReleaseCreated()
        assert event.event_type == "eaip.deploy.release.created"
        assert event.release_id == ""
        assert event.version == ""
        assert event.name == ""
        assert isinstance(event.occurred_at, datetime)

    def test_with_values(self) -> None:
        event = ReleaseCreated(
            release_id="r1",
            version="1.0.0",
            name="Release 1",
        )
        assert event.release_id == "r1"
        assert event.version == "1.0.0"
        assert event.name == "Release 1"

    def test_frozen(self) -> None:
        event = ReleaseCreated()
        with pytest.raises(ValueError):
            event.release_id = "changed"  # type: ignore[misc]


class TestReleasePromoted:
    def test_with_values(self) -> None:
        event = ReleasePromoted(
            release_id="r1",
            from_environment="staging",
            to_environment="prod",
        )
        assert event.release_id == "r1"
        assert event.from_environment == "staging"
        assert event.to_environment == "prod"
        assert event.event_type == "eaip.deploy.release.promoted"


class TestDeploymentStarted:
    def test_with_values(self) -> None:
        event = DeploymentStarted(
            deployment_id="d1",
            release_id="r1",
            environment="prod",
            strategy="rolling",
        )
        assert event.deployment_id == "d1"
        assert event.strategy == "rolling"
        assert event.event_type == "eaip.deploy.deployment.started"


class TestDeploymentCompleted:
    def test_with_values(self) -> None:
        event = DeploymentCompleted(
            deployment_id="d1",
            release_id="r1",
            environment="prod",
            duration_ms=45000,
        )
        assert event.duration_ms == 45000
        assert event.event_type == "eaip.deploy.deployment.completed"


class TestDeploymentFailed:
    def test_with_values(self) -> None:
        event = DeploymentFailed(
            deployment_id="d1",
            release_id="r1",
            environment="prod",
            error_message="timeout",
        )
        assert event.error_message == "timeout"
        assert event.event_type == "eaip.deploy.deployment.failed"


class TestDeploymentRolledBack:
    def test_with_values(self) -> None:
        event = DeploymentRolledBack(
            deployment_id="d1",
            release_id="r1",
            reason="health check failed",
        )
        assert event.reason == "health check failed"
        assert event.event_type == "eaip.deploy.deployment.rolled_back"


class TestEnvironmentUpdated:
    def test_with_values(self) -> None:
        event = EnvironmentUpdated(
            environment="prod",
            previous_version="1.0.0",
            new_version="2.0.0",
        )
        assert event.environment == "prod"
        assert event.previous_version == "1.0.0"
        assert event.new_version == "2.0.0"
        assert event.event_type == "eaip.deploy.environment.updated"


class TestDeployEvent:
    def test_type_alias(self) -> None:
        events: list[DeployEvent] = [
            ReleaseCreated(release_id="r1", version="1.0", name="R1"),
            DeploymentStarted(
                deployment_id="d1",
                release_id="r1",
                environment="prod",
                strategy="rolling",
            ),
        ]
        assert len(events) == 2
