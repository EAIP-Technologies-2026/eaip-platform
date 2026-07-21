"""Deployment & Release Management domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Release(BaseModel):
    """A named, versioned release composed of one or more artifacts."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    release_id: str
    version: str
    name: str
    description: str | None = None
    artifacts: tuple[Artifact, ...] = Field(default_factory=tuple)
    status: str = "draft"
    created_at: datetime = Field(default_factory=utc_now)
    deployed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """A deployable artifact (docker image, wheel, jar, Python package)."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    artifact_id: str
    name: str
    type: str
    uri: str
    checksum: str
    size_bytes: int


class DeploymentConfig(BaseModel):
    """Configuration for a deployment — environment, strategy, and retry settings."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    config_id: str
    environment: str
    strategy: str
    auto_rollback: bool = True
    health_check_timeout_seconds: int = 300
    max_retries: int = 3


class DeploymentLog(BaseModel):
    """A single log entry recorded during a deployment."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    timestamp: datetime = Field(default_factory=utc_now)
    level: str
    message: str
    component: str


class Deployment(BaseModel):
    """Tracks the state and progress of a single deployment run."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    deployment_id: str
    release_id: str
    environment: str
    strategy: str
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    log: tuple[DeploymentLog, ...] = Field(default_factory=tuple)
    config: DeploymentConfig


class RollbackPlan(BaseModel):
    """A structured plan to revert a deployment to a previous state."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    plan_id: str
    deployment_id: str
    reason: str
    steps: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


class EnvironmentStatus(BaseModel):
    """Current snapshot of a deployment environment's state."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    environment: str
    current_release_id: str
    health_status: str
    last_deployed_at: datetime | None = None
    version: str


__all__ = [
    "Artifact",
    "Deployment",
    "DeploymentConfig",
    "DeploymentLog",
    "EnvironmentStatus",
    "Release",
    "RollbackPlan",
]
