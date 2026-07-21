"""Domain events for consent and privacy management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ConsentRecorded(DomainEvent):
    event_type: ClassVar[str] = "consent.recorded"
    consent_id: str
    subject_id: str
    purpose: str


class ConsentUpdated(DomainEvent):
    event_type: ClassVar[str] = "consent.updated"
    consent_id: str
    subject_id: str
    new_status: str


class ConsentRevoked(DomainEvent):
    event_type: ClassVar[str] = "consent.revoked"
    consent_id: str
    subject_id: str
    purpose: str


class PrivacyPreferenceUpdated(DomainEvent):
    event_type: ClassVar[str] = "privacy.preference.updated"
    subject_id: str


class DataSubjectRequestCompleted(DomainEvent):
    event_type: ClassVar[str] = "datasubject.request.completed"
    request_id: str
    subject_id: str
    request_type: str
    status: str


__all__ = [
    "ConsentRecorded",
    "ConsentRevoked",
    "ConsentUpdated",
    "DataSubjectRequestCompleted",
    "PrivacyPreferenceUpdated",
]
