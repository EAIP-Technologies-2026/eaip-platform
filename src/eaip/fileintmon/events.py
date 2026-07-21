"""Domain events for file integrity monitoring."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class BaselineRecorded(DomainEvent):
    """Emitted when a baseline hash is recorded for a file."""

    event_type: ClassVar[str] = "eaip.fileintmon.baseline.recorded"

    file_id: str
    path: str
    hash_value: str
    algorithm: str


class IntegrityVerified(DomainEvent):
    """Emitted when a file integrity check passes."""

    event_type: ClassVar[str] = "eaip.fileintmon.integrity.verified"

    file_id: str
    path: str
    hash_matched: bool


class IntegrityViolation(DomainEvent):
    """Emitted when a file integrity check fails or a file is missing."""

    event_type: ClassVar[str] = "eaip.fileintmon.integrity.violation"

    file_id: str
    path: str
    expected_hash: str
    actual_hash: str
    reason: str


__all__ = [
    "BaselineRecorded",
    "IntegrityVerified",
    "IntegrityViolation",
]
