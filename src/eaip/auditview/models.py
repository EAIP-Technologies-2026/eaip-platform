"""Data models for the platform audit viewer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str
    action: str
    resource: str
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default=None)


class AuditFilter(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    actor: str | None = Field(default=None)
    action: str | None = Field(default=None)
    resource: str | None = Field(default=None)
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    correlation_id: str | None = Field(default=None)
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class AuditSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total: int = Field(default=0, ge=0)
    entries: tuple[AuditLogEntry, ...] = Field(default=())
    limit: int = Field(default=100)
    offset: int = Field(default=0)
    has_more: bool = Field(default=False)


class ViewerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_export_limit: int = Field(default=10000, ge=1)
    default_page_size: int = Field(default=50, ge=1)
    retention_days: int = Field(default=365, ge=1)


__all__ = [
    "AuditFilter",
    "AuditLogEntry",
    "AuditSearchResult",
    "ViewerConfig",
]
