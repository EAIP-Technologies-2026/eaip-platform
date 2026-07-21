"""Data models for document redaction."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RedactionScope(StrEnum):
    ALL = "all"
    PARTIAL = "partial"
    METADATA = "metadata"


class RedactionJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RedactionRule(BaseModel):
    """A rule defining what to redact in a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    pattern: str
    replacement: str = Field(default="[REDACTED]")
    case_sensitive: bool = Field(default=True)
    scope: RedactionScope = Field(default=RedactionScope.ALL)
    enabled: bool = Field(default=True)


class RedactionJob(BaseModel):
    """A job that applies redaction rules to a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    document_ref: str
    rules_applied: list[str] = Field(default_factory=list)
    status: RedactionJobStatus = Field(default=RedactionJobStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class RedactionConfig(BaseModel):
    """Configuration for the document redaction service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    default_replacement: str = Field(default="[REDACTED]")
    max_jobs: int = Field(default=500, ge=1)
    log_redacted_content: bool = Field(default=False)


__all__ = [
    "RedactionConfig",
    "RedactionJob",
    "RedactionJobStatus",
    "RedactionRule",
    "RedactionScope",
]
