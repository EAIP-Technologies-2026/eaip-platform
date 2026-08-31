"""Data models for blue-green deployment management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EnvironmentType(StrEnum):
    """Type of deployment environment."""

    BLUE = "blue"
    GREEN = "green"


class EnvironmentStatus(StrEnum):
    """Status of a deployment environment."""

    ACTIVE = "active"
    STANDBY = "standby"
    DRAINING = "draining"


class SwitchStrategy(StrEnum):
    """Strategy for switching traffic between environments."""

    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    HEALTH_CHECK = "health_check"


class Environment(BaseModel):
    """A deployment environment (blue or green)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: EnvironmentType
    status: EnvironmentStatus = Field(default=EnvironmentStatus.STANDBY)
    version: str = Field(default="")
    deployed_at: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class DeploymentSwitch(BaseModel):
    """A traffic switch operation between environments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_env: str
    to_env: str
    strategy: SwitchStrategy = Field(default=SwitchStrategy.HEALTH_CHECK)
    health_check_required: bool = Field(default=True)
    traffic_weight: int = Field(default=100, ge=0, le=100)
    switched_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class BlueGreenConfig(BaseModel):
    """Configuration for the blue-green deployment manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    health_check_timeout_seconds: int = Field(default=300, ge=1)
    drain_timeout_seconds: int = Field(default=120, ge=0)
    gradual_step_percent: int = Field(default=10, ge=1, le=100)
    auto_rollback_enabled: bool = Field(default=True)
    max_switch_attempts: int = Field(default=3, ge=1)


__all__ = [
    "BlueGreenConfig",
    "DeploymentSwitch",
    "Environment",
    "EnvironmentStatus",
    "EnvironmentType",
    "SwitchStrategy",
]
