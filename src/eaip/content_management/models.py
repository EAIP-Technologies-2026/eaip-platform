"""Content management domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContentStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    ARCHIVED = "archived"


class ContentType(StrEnum):
    ARTICLE = "article"
    BLOG = "blog"
    PAGE = "page"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    TEMPLATE = "template"
    CONFIG = "config"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ContentWorkflowStatus(StrEnum):
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
    body: str
    version: str = "0.1.0"
    status: ContentStatus = ContentStatus.DRAFT
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    published_at: datetime | None = None
    author: str = ""


class ContentCollection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    items: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ContentCategory(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    slug: str = ""
    description: str = ""
    parent_id: str | None = None


class ContentTag(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    slug: str = ""


class ContentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    key: str
    value: str
    created_at: datetime = Field(default_factory=utc_now)


class ContentVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    version: str
    body: str
    change_log: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ContentReview(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    reviewer: str
    decision: ReviewDecision
    comments: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ContentPublishSchedule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    publish_at: datetime
    expire_at: datetime | None = None
    published: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class ContentWorkflow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    item_id: str
    status: ContentWorkflowStatus = ContentWorkflowStatus.PENDING
    steps: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class ContentTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    body: str
    variables: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


class ContentLocalization(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    locale: str
    title: str = ""
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ContentDeliveryRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    condition: str = ""
    priority: int = 0
    target_audience: str = ""
    active: bool = True


class ContentAnalytics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    views: int = 0
    unique_visitors: int = 0
    avg_read_time_seconds: float = 0.0
    collected_at: datetime = Field(default_factory=utc_now)


class ContentPermission(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    principal: str
    permission: str
    granted_at: datetime = Field(default_factory=utc_now)


class ContentSubscription(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    item_id: str
    subscriber: str
    event_types: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ContentAnalytics",
    "ContentCategory",
    "ContentCollection",
    "ContentDeliveryRule",
    "ContentItem",
    "ContentLocalization",
    "ContentMetadata",
    "ContentPermission",
    "ContentPublishSchedule",
    "ContentReview",
    "ContentStatus",
    "ContentSubscription",
    "ContentTag",
    "ContentTemplate",
    "ContentType",
    "ContentVersion",
    "ContentWorkflow",
    "ContentWorkflowStatus",
    "ReviewDecision",
]
