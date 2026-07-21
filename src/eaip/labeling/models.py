"""Data models for data labeling — tasks, labels, assignments, and config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LabelingTask(BaseModel):
    """A data labeling task definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    status: str = Field(default="pending")
    data_ref: str = Field(default="")
    labels: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Label(BaseModel):
    """A single label submitted by a labeler."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    task_id: str
    labeler_id: str
    value: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    reviewed: bool = Field(default=False)
    submitted_at: datetime = Field(default_factory=utc_now)


class LabelerAssignment(BaseModel):
    """An assignment of a labeler to a labeling task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    labeler_id: str
    assigned_at: datetime = Field(default_factory=utc_now)
    completed: bool = Field(default=False)


class LabelingConfig(BaseModel):
    """Configuration for the data labeling engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_labelers_per_task: int = Field(default=1, ge=1)
    max_labelers_per_task: int = Field(default=5, ge=1)
    require_review: bool = Field(default=True)
    auto_approve_threshold: float = Field(default=0.9, ge=0, le=1)


__all__ = [
    "Label",
    "LabelerAssignment",
    "LabelingConfig",
    "LabelingTask",
]
