"""Data models for Infrastructure as Code validation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class IaCType(StrEnum):
    CLOUD_FORMATION = "cloud_formation"
    TERRAFORM = "terraform"
    PULUMI = "pulumi"
    ANSIBLE = "ansible"


class IaCTemplateStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class CheckType(StrEnum):
    SYNTAX = "syntax"
    POLICY = "policy"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class IaCTemplate(BaseModel):
    """An Infrastructure as Code template registered for validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: IaCType
    content_ref: str
    version: str = Field(default="1.0")
    status: IaCTemplateStatus = Field(default=IaCTemplateStatus.UNKNOWN)


class ValidationCheck(BaseModel):
    """The result of a single validation check against an IaC template."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    template_id: str
    check_type: CheckType
    passed: bool = Field(default=True)
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=utc_now)


class ValidatorConfig(BaseModel):
    """Configuration for the IaC validator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_checks_per_template: int = Field(default=50, ge=1)
    fail_on_policy_violation: bool = Field(default=True)
    fail_on_security_violation: bool = Field(default=True)
    fail_on_compliance_violation: bool = Field(default=False)


__all__ = [
    "CheckType",
    "IaCTemplate",
    "IaCTemplateStatus",
    "IaCType",
    "ValidationCheck",
    "ValidatorConfig",
]
