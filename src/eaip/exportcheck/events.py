"""Domain events for export compliance checking."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.exportcheck.models import ScreeningStatus


class PartyScreened(DomainEvent):
    """Emitted when a party is screened against restricted lists."""

    event_type: ClassVar[str] = "eaip.exportcheck.party.screened"

    party_name: str
    match_score: float
    status: ScreeningStatus


class MatchFlagged(DomainEvent):
    """Emitted when a screening match is flagged for review."""

    event_type: ClassVar[str] = "eaip.exportcheck.match.flagged"

    party_name: str
    match_score: float
    matched_list: str


class RuleUpdated(DomainEvent):
    """Emitted when a compliance rule or list is updated."""

    event_type: ClassVar[str] = "eaip.exportcheck.rule.updated"

    rule_id: str
    list_type: str
    action: str


__all__ = [
    "MatchFlagged",
    "PartyScreened",
    "RuleUpdated",
]
