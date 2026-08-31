"""Domain events emitted by the change log service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ChangeRecorded(DomainEvent):
    """Emitted when a single change is recorded in the change log."""

    event_type: ClassVar[str] = "eaip.changelogsvc.change_recorded"

    entry_id: str
    resource_id: str
    resource_type: str
    action: str


class ChangeBatchProcessed(DomainEvent):
    """Emitted when a batch of changes has been processed."""

    event_type: ClassVar[str] = "eaip.changelogsvc.change_batch_processed"

    batch_size: int
    success_count: int
    failure_count: int
