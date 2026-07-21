"""Domain events for firewall rule management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class RuleCreated(DomainEvent):
    """Emitted when a firewall rule is created."""

    event_type: ClassVar[str] = "eaip.firewall.rule.created"

    rule_id: str
    name: str
    action: str
    environment: str


class RuleUpdated(DomainEvent):
    """Emitted when a firewall rule is updated."""

    event_type: ClassVar[str] = "eaip.firewall.rule.updated"

    rule_id: str
    changes: dict[str, str]


class RuleDeleted(DomainEvent):
    """Emitted when a firewall rule is deleted."""

    event_type: ClassVar[str] = "eaip.firewall.rule.deleted"

    rule_id: str
    name: str


class RuleSetActivated(DomainEvent):
    """Emitted when a rule set is activated."""

    event_type: ClassVar[str] = "eaip.firewall.ruleset.activated"

    ruleset_id: str
    name: str
    rule_count: int
    environment: str


__all__ = [
    "RuleCreated",
    "RuleDeleted",
    "RuleSetActivated",
    "RuleUpdated",
]
