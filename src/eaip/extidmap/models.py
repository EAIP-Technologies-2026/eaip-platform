"""Data models for external identity mapping — mappings, rules, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MappingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    REVOKED = "REVOKED"


class IdentityMapping(BaseModel):
    """A mapping between a local identity and an external identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    local_uid: str
    external_uid: str
    external_idp: str = Field(default="")
    attributes: dict[str, Any] = Field(default_factory=dict)
    mapped_at: datetime = Field(default_factory=utc_now)
    status: MappingStatus


class MappingRule(BaseModel):
    """A rule that defines how fields are mapped between identity systems."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_field: str
    target_field: str
    transformation: str = Field(default="direct")


class MapperConfig(BaseModel):
    """Configuration for the external identity mapper."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    default_idp: str = Field(default="azure_ad")
    stale_after_days: int = Field(default=90, ge=1)
    auto_revoke_stale: bool = Field(default=False)


__all__ = [
    "IdentityMapping",
    "MapperConfig",
    "MappingRule",
    "MappingStatus",
]
