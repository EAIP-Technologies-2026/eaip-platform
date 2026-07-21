"""IP reputation models — reputation data, check records, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class IPCategory(StrEnum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    KNOWN = "known"


class ReputationScore(IntEnum):
    SAFE = 0
    LOW = 25
    MEDIUM = 50
    HIGH = 75
    CRITICAL = 100


class IPReputation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ip: str
    score: int = Field(default=0, ge=0, le=100)
    category: IPCategory = IPCategory.SAFE
    threat_type: str = ""
    first_seen: datetime | None = None
    last_seen: datetime = Field(default_factory=utc_now)
    source_feed: str = ""


class ReputationCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    ip: str
    score: int = Field(default=0, ge=0, le=100)
    action: str = ""
    checked_at: datetime = Field(default_factory=utc_now)


class ReputationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    suspicious_threshold: int = Field(default=30, ge=0, le=100)
    malicious_threshold: int = Field(default=70, ge=0, le=100)
    cache_ttl_seconds: int = Field(default=300, ge=0)
    max_blocklist_entries: int = Field(default=10000, ge=1)
    enable_auto_blocklist: bool = Field(default=True)


__all__ = [
    "IPCategory",
    "IPReputation",
    "ReputationCheck",
    "ReputationConfig",
    "ReputationScore",
]
