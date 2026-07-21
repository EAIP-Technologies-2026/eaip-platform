"""Data models for firewall rule management — rules, rule sets, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RuleAction(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    LOG = "LOG"


class RuleSetStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"


class FirewallRule(BaseModel):
    """A single firewall rule definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source: str = Field(default="*")
    destination: str = Field(default="*")
    port: int | None = Field(default=None, ge=1, le=65535)
    protocol: str = Field(default="tcp")
    action: RuleAction
    priority: int = Field(default=100, ge=0, le=10000)
    enabled: bool = Field(default=True)
    environment: str = Field(default="production")


class RuleSet(BaseModel):
    """A named collection of firewall rules."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    rules: tuple[FirewallRule, ...] = Field(default=())
    environment: str = Field(default="production")
    status: RuleSetStatus = Field(default=RuleSetStatus.DRAFT)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FirewallConfig(BaseModel):
    """Configuration for the firewall rule manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    default_action: RuleAction = Field(default=RuleAction.DENY)
    max_rules_per_set: int = Field(default=500, ge=1)
    enforce_tls: bool = Field(default=True)


__all__ = [
    "FirewallConfig",
    "FirewallRule",
    "RuleAction",
    "RuleSet",
    "RuleSetStatus",
]
