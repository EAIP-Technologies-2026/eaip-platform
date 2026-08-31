"""Data models for export compliance — restricted parties, screening results, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ScreeningStatus(StrEnum):
    CLEAR = "CLEAR"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"


class RestrictedParty(BaseModel):
    """A person or entity on a restricted/sanctions list."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    aliases: tuple[str, ...] = Field(default=())
    country: str = Field(default="")
    list_type: str = Field(default="")
    sanctions: tuple[str, ...] = Field(default=())
    added_at: datetime = Field(default_factory=utc_now)


class ScreeningResult(BaseModel):
    """Result of screening a party against restricted lists."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    party_name: str
    match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_rules: tuple[str, ...] = Field(default=())
    status: ScreeningStatus
    screened_at: datetime = Field(default_factory=utc_now)


class ComplianceConfig(BaseModel):
    """Configuration for export compliance screening."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    min_match_score: float = Field(default=0.8, ge=0.0, le=1.0)
    auto_block_above: float = Field(default=0.95, ge=0.0, le=1.0)
    lists: tuple[str, ...] = Field(default=("sdn", "consolidated", "eu"))


__all__ = [
    "ComplianceConfig",
    "RestrictedParty",
    "ScreeningResult",
    "ScreeningStatus",
]
