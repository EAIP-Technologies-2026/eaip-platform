"""Content domain models - ContentItem, ContentVersion, PublishingWorkflow, WorkflowStep, ContentConfig."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContentType(StrEnum):
    DOCUMENT = "document"
    IMAGE = "image"
    CONFIG = "config"
    TEMPLATE = "template"
    SCRIPT = "script"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class WorkflowStepType(StrEnum):
    REVIEW = "review"
    APPROVAL = "approval"
    PUBLISH = "publish"
    NOTIFY = "notify"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: ContentType
    content_type: str
    body: str
    version: str = "0.1.0"
    status: ContentStatus = ContentStatus.DRAFT
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    published_at: datetime | None = None
    author: str = ""
    checksum: str = ""
    content_hash: str = ""


class ContentVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    version: str
    body: str
    checksum: str = ""
    change_log: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: WorkflowStepType
    assignees: tuple[str, ...] = Field(default_factory=tuple)
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    timeout_hours: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublishingWorkflow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    steps: tuple[WorkflowStep, ...] = Field(default_factory=tuple)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)


class ContentConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_versions_per_item: int = 10
    enable_versioning: bool = True
    enable_workflow: bool = True
    default_status: ContentStatus = ContentStatus.DRAFT
    storage_backend: str = "memory"
    cache_ttl_seconds: int = 300
    allowed_types: tuple[ContentType, ...] = Field(default_factory=lambda: tuple(ContentType))


__all__ = [
    "ContentConfig",
    "ContentItem",
    "ContentStatus",
    "ContentType",
    "ContentVersion",
    "PublishingWorkflow",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepStatus",
    "WorkflowStepType",
]
