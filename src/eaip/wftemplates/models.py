"""Workflow Template models — WorkflowTemplate, WorkflowTemplateCategory, TemplateSearchFilter."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TemplateStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WorkflowTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    category: str = ""
    industry: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    steps: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    edges: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    config: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
    rating: float = 0.0
    download_count: int = 0
    author: str = ""
    status: TemplateStatus = TemplateStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowTemplateCategory(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    icon: str = ""
    parent: str | None = None
    order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TemplateSearchFilter(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    category: str | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple)
    industry: str | None = None
    min_rating: float = 0.0
    sort_by: str = "download_count"
    page: int = 1
    page_size: int = 20


__all__ = [
    "TemplateSearchFilter",
    "TemplateStatus",
    "WorkflowTemplate",
    "WorkflowTemplateCategory",
]
