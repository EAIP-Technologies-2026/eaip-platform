"""Pydantic models for compliance frameworks, scans, and findings."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FindingStatus(StrEnum):
    """Status of a compliance finding."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NA = "na"


class ComplianceFramework(BaseModel):
    """A compliance framework with version and controls."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    controls: tuple[str, ...] = Field(default=())


class ComplianceScan(BaseModel):
    """Result of a compliance scan against a target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    framework_id: str
    target: str
    status: str = "pending"
    findings: tuple[str, ...] = Field(default=())
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class ComplianceFinding(BaseModel):
    """A single finding from a compliance scan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    scan_id: str
    control_id: str
    status: FindingStatus
    evidence: str = ""
    details: str = ""


class GeneratorConfig(BaseModel):
    """Configuration settings for the compliance report generator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_findings_per_scan: int = 1000
    default_framework: str = "nist-800-53"
    include_evidence: bool = True
    output_format: str = "json"
