"""Domain events for diagnostic data collection."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ReportCollected(DomainEvent):
    """Emitted when a diagnostic report is collected."""

    event_type: ClassVar[str] = "eaip.diagnostic.report.collected"

    report_id: str
    component: str
    category: str
    severity: str


class RuleCreated(DomainEvent):
    """Emitted when a collection rule is created."""

    event_type: ClassVar[str] = "eaip.diagnostic.rule.created"

    rule_id: str
    name: str
    component: str
    metric_path: str


class RuleUpdated(DomainEvent):
    """Emitted when a collection rule is updated."""

    event_type: ClassVar[str] = "eaip.diagnostic.rule.updated"

    rule_id: str
    name: str
    enabled: bool


__all__ = [
    "ReportCollected",
    "RuleCreated",
    "RuleUpdated",
]
