"""Domain events for deployment & release management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ReleaseCreated(DomainEvent):
    """Emitted when a new release is created."""

    event_type: ClassVar[str] = "eaip.deploy.release.created"
    release_id: str = ""
    version: str = ""
    name: str = ""


class ReleasePromoted(DomainEvent):
    """Emitted when a release is promoted from one environment to another."""

    event_type: ClassVar[str] = "eaip.deploy.release.promoted"
    release_id: str = ""
    from_environment: str = ""
    to_environment: str = ""


class DeploymentStarted(DomainEvent):
    """Emitted when a deployment begins execution."""

    event_type: ClassVar[str] = "eaip.deploy.deployment.started"
    deployment_id: str = ""
    release_id: str = ""
    environment: str = ""
    strategy: str = ""


class DeploymentCompleted(DomainEvent):
    """Emitted when a deployment completes successfully."""

    event_type: ClassVar[str] = "eaip.deploy.deployment.completed"
    deployment_id: str = ""
    release_id: str = ""
    environment: str = ""
    duration_ms: int = 0


class DeploymentFailed(DomainEvent):
    """Emitted when a deployment fails."""

    event_type: ClassVar[str] = "eaip.deploy.deployment.failed"
    deployment_id: str = ""
    release_id: str = ""
    environment: str = ""
    error_message: str = ""


class DeploymentRolledBack(DomainEvent):
    """Emitted when a deployment is rolled back."""

    event_type: ClassVar[str] = "eaip.deploy.deployment.rolled_back"
    deployment_id: str = ""
    release_id: str = ""
    reason: str = ""


class EnvironmentUpdated(DomainEvent):
    """Emitted when an environment's deployed version changes."""

    event_type: ClassVar[str] = "eaip.deploy.environment.updated"
    environment: str = ""
    previous_version: str = ""
    new_version: str = ""


DeployEvent = (
    ReleaseCreated
    | ReleasePromoted
    | DeploymentStarted
    | DeploymentCompleted
    | DeploymentFailed
    | DeploymentRolledBack
    | EnvironmentUpdated
)


__all__ = [
    "DeployEvent",
    "DeploymentCompleted",
    "DeploymentFailed",
    "DeploymentRolledBack",
    "DeploymentStarted",
    "EnvironmentUpdated",
    "ReleaseCreated",
    "ReleasePromoted",
]
