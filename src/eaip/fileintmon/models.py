"""Data models for file integrity monitoring — files, checks, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FileStatus(StrEnum):
    BASELINE = "BASELINE"
    CHANGED = "CHANGED"
    NEW = "NEW"
    DELETED = "DELETED"


class MonitoredFile(BaseModel):
    """A file being monitored for integrity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    path: str
    checksum_algorithm: str = Field(default="sha256")
    baseline_hash: str = Field(default="")
    last_verified_at: datetime | None = Field(default=None)
    status: FileStatus


class IntegrityCheck(BaseModel):
    """Result of an integrity check on a monitored file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    file_id: str
    expected_hash: str = Field(default="")
    actual_hash: str = Field(default="")
    match: bool
    checked_at: datetime = Field(default_factory=utc_now)


class MonitorConfig(BaseModel):
    """Configuration for file integrity monitoring."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    checksum_algorithm: str = Field(default="sha256")
    check_interval_seconds: int = Field(default=3600, ge=60)
    alert_on_change: bool = Field(default=True)
    alert_on_new: bool = Field(default=True)
    alert_on_delete: bool = Field(default=True)


__all__ = [
    "FileStatus",
    "IntegrityCheck",
    "MonitorConfig",
    "MonitoredFile",
]
