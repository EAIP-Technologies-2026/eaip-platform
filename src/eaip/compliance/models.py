"""Pydantic models for the compliance & regulatory framework."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Regulation(BaseModel):
    """A regulatory framework (e.g. GDPR, SOC2, HIPAA)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    regulation_id: str = Field(description="Unique identifier for the regulation")
    name: str = Field(description="Human-readable name of the regulation")
    description: str = Field(description="Description of the regulation")
    version: str = Field(description="Version string for the regulation")
    required_controls: tuple[str, ...] = Field(
        default=(),
        description="Control IDs required by this regulation",
    )


class Control(BaseModel):
    """A control required by a regulation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    control_id: str = Field(description="Unique identifier for the control")
    regulation_id: str = Field(description="Regulation this control belongs to")
    category: str = Field(description="Category of the control")
    description: str = Field(description="Description of the control")
    severity: str = Field(description="Severity: critical, high, medium, low")
    status: str = Field(description="Status: compliant, non_compliant, not_applicable, unknown")


class ComplianceReport(BaseModel):
    """A report summarising compliance scan results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str = Field(description="Unique identifier for the report")
    generated_at: datetime = Field(description="When the report was generated")
    regulation_id: str = Field(description="Regulation this report covers")
    overall_status: str = Field(description="Overall compliance status")
    controls: tuple[Control, ...] = Field(
        default=(),
        description="Controls evaluated in this report",
    )
    total_controls: int = Field(description="Total number of controls evaluated")
    compliant_count: int = Field(description="Number of compliant controls")
    non_compliant_count: int = Field(description="Number of non-compliant controls")
    score: float = Field(description="Compliance score (0.0 - 100.0)")


class ComplianceScanConfig(BaseModel):
    """Configuration for compliance scanning."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    regulations: tuple[str, ...] = Field(description="Regulations to scan")
    scan_interval_hours: int = Field(default=24, description="Interval between scans in hours")
    auto_remediate: bool = Field(default=False, description="Whether to auto-remediate findings")
    notify_on_findings: bool = Field(default=True, description="Whether to notify on findings")


class EvidenceRecord(BaseModel):
    """Record of collected evidence for a control."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str = Field(description="Unique identifier for the evidence")
    control_id: str = Field(description="Control this evidence supports")
    source: str = Field(description="Source of the evidence")
    timestamp: datetime = Field(description="When the evidence was collected")
    data: dict[str, Any] = Field(description="Evidence data payload")
    collected_by: str = Field(description="Collector that gathered this evidence")
    valid: bool = Field(default=True, description="Whether the evidence is still valid")


class RemediationItem(BaseModel):
    """A remediation action item for a non-compliant control."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str = Field(description="Unique identifier for the remediation item")
    control_id: str = Field(description="Control this item addresses")
    description: str = Field(description="Description of the remediation")
    status: str = Field(description="Status: open, in_progress, resolved, waived")
    created_at: datetime = Field(default_factory=utc_now, description="When the item was created")
    resolved_at: datetime | None = Field(default=None, description="When the item was resolved")
    assigned_to: str | None = Field(default=None, description="Who this item is assigned to")
