"""Domain events for Infrastructure as Code validation."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.iacvalid.models import CheckType, IaCType


class TemplateRegistered(DomainEvent):
    """Emitted when a new IaC template is registered."""

    event_type: ClassVar[str] = "eaip.iacvalid.template.registered"

    template_id: str
    name: str
    type: IaCType


class ValidationStarted(DomainEvent):
    """Emitted when a validation run begins."""

    event_type: ClassVar[str] = "eaip.iacvalid.validation.started"

    template_id: str
    name: str
    check_types: tuple[CheckType, ...]


class ValidationCompleted(DomainEvent):
    """Emitted when a validation run completes."""

    event_type: ClassVar[str] = "eaip.iacvalid.validation.completed"

    template_id: str
    name: str
    checks_passed: int
    checks_failed: int
    total_checks: int


class ViolationFound(DomainEvent):
    """Emitted when a validation violation is detected."""

    event_type: ClassVar[str] = "eaip.iacvalid.violation.found"

    template_id: str
    check_id: str
    check_type: CheckType
    details: dict[str, Any]


__all__ = [
    "TemplateRegistered",
    "ValidationCompleted",
    "ValidationStarted",
    "ViolationFound",
]
