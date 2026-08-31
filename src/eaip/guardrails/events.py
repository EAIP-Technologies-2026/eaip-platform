"""Domain events for the AI Guardrails engine."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class InputValidated(DomainEvent):
    """Emitted when an input is validated against guardrail rules."""

    event_type: ClassVar[str] = "eaip.guardrails.input.validated"

    input_id: str
    rule_id: str
    passed: bool
    violations: tuple[str, ...] = Field(default=())


class OutputChecked(DomainEvent):
    """Emitted when an output is checked against guardrail rules."""

    event_type: ClassVar[str] = "eaip.guardrails.output.checked"

    output_id: str
    rule_id: str
    passed: bool
    issues: tuple[str, ...] = Field(default=())


class GuardrailTriggered(DomainEvent):
    """Emitted when a guardrail rule is triggered."""

    event_type: ClassVar[str] = "eaip.guardrails.rule.triggered"

    rule_id: str
    input_id: str
    action: str
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "GuardrailTriggered",
    "InputValidated",
    "OutputChecked",
]
