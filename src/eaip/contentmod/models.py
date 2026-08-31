"""Content moderation domain models — items, rules, results, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContentStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ModerationAction(StrEnum):
    FLAG = "flag"
    BLOCK = "block"
    REVIEW = "review"


class ContentItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: str
    content_type: str
    text_content: str
    status: ContentStatus = ContentStatus.PENDING
    submitted_by: str
    submitted_at: datetime = Field(default_factory=utc_now)


class ModerationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    pattern: str
    action: ModerationAction
    priority: int = 0


class ModerationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    content_id: str
    rule_id: str
    action: ModerationAction
    reason: str = ""
    moderated_at: datetime = Field(default_factory=utc_now)


class ContentModerationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_approve: bool = False
    max_rule_priority: int = 100
    enable_flagging: bool = True
    enable_blocking: bool = True
    default_action: ModerationAction = ModerationAction.REVIEW


__all__ = [
    "ContentItem",
    "ContentModerationConfig",
    "ContentStatus",
    "ModerationAction",
    "ModerationResult",
    "ModerationRule",
]
