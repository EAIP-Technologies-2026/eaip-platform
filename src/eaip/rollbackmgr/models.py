"""Data models for deployment rollback — deployments, plans, executions, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RollbackStrategy(StrEnum):
    """Rollback execution strategies."""

    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    CANARY = "canary"


class Deployment(BaseModel):
    """A record of a deployment that can be rolled back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    environment: str
    status: str = Field(default="deployed")
    deployed_at: datetime = Field(default_factory=utc_now)
    deployed_by: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RollbackPlan(BaseModel):
    """A plan describing how to roll back a deployment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    deployment_id: str
    strategy: RollbackStrategy = Field(default=RollbackStrategy.IMMEDIATE)
    steps: tuple[str, ...] = Field(default=())
    estimated_duration: int = Field(default=0, ge=0)
    auto_approve: bool = Field(default=False)


class RollbackExecution(BaseModel):
    """A record of a rollback execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    deployment_id: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    success: bool = Field(default=False)
    output: str = Field(default="")
    error_message: str = Field(default="")


class RollbackConfig(BaseModel):
    """Configuration for the rollback manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    require_approval: bool = Field(default=True)
    max_retries: int = Field(default=2, ge=0)
    health_check_before_rollback: bool = Field(default=True)
    notify_on_failure: bool = Field(default=True)


__all__ = [
    "Deployment",
    "RollbackConfig",
    "RollbackExecution",
    "RollbackPlan",
    "RollbackStrategy",
]
