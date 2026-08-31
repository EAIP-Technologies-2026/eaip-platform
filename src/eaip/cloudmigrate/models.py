"""Pydantic models for cloud migration assessments, plans, and tasks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MigrationAssessment(BaseModel):
    """Result of a migration readiness assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: str
    target: str
    resources: tuple[str, ...] = Field(default=())
    estimated_cost: float = 0.0
    risks: tuple[str, ...] = Field(default=())
    score: float = 0.0


class MigrationPlan(BaseModel):
    """A migration plan derived from an assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    assessment_id: str
    steps: tuple[str, ...] = Field(default=())
    timeline: str = ""
    rollback_strategy: str = ""


class MigrationTask(BaseModel):
    """A single task within a migration plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    name: str
    description: str = ""
    order: int = 0
    status: str = "pending"


class MigrationConfig(BaseModel):
    """Configuration settings for the cloud migration assistant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_tasks: int = 5
    default_region: str = "eastus"
    enable_validation: bool = True
    rollback_on_failure: bool = False
