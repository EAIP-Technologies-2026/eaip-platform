"""Data models for backup verification — records, verification results, and config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class BackupRecord(BaseModel):
    """A single backup record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    backup_type: str = Field(default="full")
    status: str = Field(default="completed")
    size_bytes: int = Field(default=0, ge=0)
    checksum: str = Field(default="")
    location: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    verified_at: datetime | None = Field(default=None)
    verified: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """The result of a backup verification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    verified: bool = Field(default=False)
    integrity_pass: bool = Field(default=False)
    recovery_test_pass: bool = Field(default=False)
    duration_ms: int = Field(default=0, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    verified_at: datetime = Field(default_factory=utc_now)


class VerificationConfig(BaseModel):
    """Configuration for backup verification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    verify_integrity: bool = Field(default=True)
    run_recovery_test: bool = Field(default=False)
    checksum_algorithm: str = Field(default="sha256")
    max_verification_duration_ms: int = Field(default=300000, ge=0)


__all__ = [
    "BackupRecord",
    "VerificationConfig",
    "VerificationResult",
]
