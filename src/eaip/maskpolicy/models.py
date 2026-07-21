"""Data masking policy domain models — rules, policies, config."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class MaskingRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    pattern: str = Field(default="")
    mask_char: str = Field(default="*")
    preserve_length: bool = Field(default=True)
    preserve_prefix: int = Field(default=0)
    apply_to_fields: tuple[str, ...] = Field(default=())
    enabled: bool = Field(default=True)


class MaskingPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    rules: tuple[MaskingRule, ...] = Field(default=())
    data_types: tuple[str, ...] = Field(default=())
    environment: str = Field(default="production")
    status: PolicyStatus = Field(default=PolicyStatus.DRAFT)


class MaskingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_mask_char: str = Field(default="*")
    enable_audit_logging: bool = Field(default=True)
    max_policies: int = Field(default=50)


__all__ = [
    "MaskingConfig",
    "MaskingPolicy",
    "MaskingRule",
    "PolicyStatus",
]
