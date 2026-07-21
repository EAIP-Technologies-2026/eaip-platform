"""Domain events for the platform audit viewer."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class EntryIngested(DomainEvent):
    event_type: ClassVar[str] = "eaip.auditview.entry.ingested"

    entry_id: str
    actor: str
    action: str
    resource: str


class AuditExported(DomainEvent):
    event_type: ClassVar[str] = "eaip.auditview.audit.exported"

    filter_actor: str | None
    filter_action: str | None
    filter_resource: str | None
    entry_count: int


__all__ = [
    "AuditExported",
    "EntryIngested",
]
