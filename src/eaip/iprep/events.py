"""Domain events for the IP reputation service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.iprep.models import IPCategory


class IPChecked(DomainEvent):
    event_type: ClassVar[str] = "eaip.iprep.ip_checked"

    ip: str
    score: int
    category: IPCategory


class BlocklistUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.iprep.blocklist_updated"

    ip: str
    reason: str
    entries_count: int


class ReputationChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.iprep.reputation_changed"

    ip: str
    old_score: int
    new_score: int
    old_category: IPCategory
    new_category: IPCategory


__all__ = [
    "BlocklistUpdated",
    "IPChecked",
    "ReputationChanged",
]
