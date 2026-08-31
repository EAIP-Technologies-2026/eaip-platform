"""Container domain models — container definitions, deployments, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContainerStatus(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    PENDING = "pending"


class Container(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    image: str
    status: ContainerStatus = ContainerStatus.PENDING
    port: int | None = None
    resources: dict[str, Any] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ContainerDeployment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    container_id: str
    replicas: int = 1
    strategy: str = "rolling"
    exposed_ports: tuple[int, ...] = Field(default=())
    env_vars: dict[str, str] = Field(default_factory=dict)


class ContainerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_replicas: int = 1
    max_replicas: int = 10
    default_strategy: str = "rolling"
    health_check_interval_seconds: int = 30
    restart_policy: str = "always"


__all__ = [
    "Container",
    "ContainerConfig",
    "ContainerDeployment",
    "ContainerStatus",
]
