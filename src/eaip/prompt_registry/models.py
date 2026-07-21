"""Prompt Registry domain models — prompts, versions, categories, tags, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PromptStatus(StrEnum):
    """Status of a prompt definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class PromptVersionStatus(StrEnum):
    """Status of a specific prompt version."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    ARCHIVED = "archived"


class PromptApprovalStatus(StrEnum):
    """Approval status for prompt reviews."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PromptCategory(StrEnum):
    """Category classification for prompts."""

    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    CUSTOM = "custom"


class PromptVariable(BaseModel):
    """A named variable that can be substituted into a prompt template."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str = "string"
    required: bool = False
    default: str = ""
    description: str = ""


class PromptParameter(BaseModel):
    """A configurable parameter for a prompt template."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    param_id: str = ""
    name: str
    type: str = "string"
    required: bool = False
    default: str = ""
    description: str = ""


class PromptTag(BaseModel):
    """A tag for categorising and filtering prompts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tag_id: str = ""
    name: str
    description: str = ""
    color: str = ""


class PromptMetadata(BaseModel):
    """A key-value metadata entry for a prompt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str = ""


class PromptTemplate(BaseModel):
    """A reusable prompt template with variables, parameters, and metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str
    name: str
    description: str = ""
    content: str
    version: str = "1.0.0"
    variables: tuple[PromptVariable, ...] = ()
    parameters: tuple[PromptParameter, ...] = ()
    category: PromptCategory = PromptCategory.CUSTOM
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PromptVersion(BaseModel):
    """A specific versioned snapshot of a prompt's content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_id: str = ""
    prompt_id: str
    version: str
    content: str
    change_log: str = ""
    author: str = ""
    status: PromptVersionStatus = PromptVersionStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PromptDefinition(BaseModel):
    """Top-level definition of a prompt in the registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_id: str
    name: str
    description: str = ""
    current_version: str = "1.0.0"
    category: PromptCategory = PromptCategory.CUSTOM
    status: PromptStatus = PromptStatus.DRAFT
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str = ""


class PromptRegistryConfig(BaseModel):
    """Configuration for the Prompt Registry subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    storage_backend: str = "memory"
    max_versions_per_prompt: int = 50
    auto_versioning: bool = False
    event_bus_enabled: bool = True


class PromptSearchResult(BaseModel):
    """Paginated result of a prompt search query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total: int = 0
    results: tuple[PromptDefinition, ...] = ()
    page: int = 1
    page_size: int = 20


class PromptDiffResult(BaseModel):
    """Result of comparing two prompt versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_a: str
    version_b: str
    additions: tuple[str, ...] = ()
    removals: tuple[str, ...] = ()
    modifications: tuple[str, ...] = ()
    summary: str = ""


__all__ = [
    "PromptApprovalStatus",
    "PromptCategory",
    "PromptDefinition",
    "PromptDiffResult",
    "PromptMetadata",
    "PromptParameter",
    "PromptRegistryConfig",
    "PromptSearchResult",
    "PromptStatus",
    "PromptTag",
    "PromptTemplate",
    "PromptVariable",
    "PromptVersion",
    "PromptVersionStatus",
]
