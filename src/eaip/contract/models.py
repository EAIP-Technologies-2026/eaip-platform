"""Contract domain models — contracts, versions, and configuration."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContractStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    parties: tuple[str, ...]
    type: str
    status: ContractStatus = ContractStatus.DRAFT
    start_date: date
    end_date: date | None = None
    terms: str = ""
    value: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContractVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    contract_id: str
    version: int = 1
    content: str = ""
    change_summary: str = ""
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)


class ContractConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_archive_days: int = 365
    max_versions: int = 50
    require_approval: bool = True
    enable_versioning: bool = True
    default_currency: str = "USD"


__all__ = [
    "Contract",
    "ContractConfig",
    "ContractStatus",
    "ContractVersion",
]
