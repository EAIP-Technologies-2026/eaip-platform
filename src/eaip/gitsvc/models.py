"""Data models for Git integration — repositories, commits, webhooks, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GitRepositoryStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class GitRepository(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    url: str
    branch: str = Field(default="main")
    provider: str = Field(default="github")
    webhook_secret: str | None = Field(default=None)
    status: GitRepositoryStatus = Field(default=GitRepositoryStatus.ACTIVE)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GitCommit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    repo_id: str
    sha: str
    author: str
    message: str
    timestamp: datetime
    files_changed: int = Field(default=0)


class GitWebhookEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    repo_id: str
    event_type: str
    payload: dict[str, object] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=utc_now)


class GitConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_branch: str = Field(default="main")
    webhook_retry_limit: int = Field(default=3, ge=0)
    clone_timeout_seconds: int = Field(default=300, ge=1)
    allowed_providers: tuple[str, ...] = Field(default=("github", "gitlab", "bitbucket"))


__all__ = [
    "GitCommit",
    "GitConfig",
    "GitRepository",
    "GitRepositoryStatus",
    "GitWebhookEvent",
]
