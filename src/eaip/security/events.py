"""Domain events for the security module."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.shared.time import utc_now


class SecretStored(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.secret.stored"
    secret_id: str
    secret_name: str
    secret_type: str


class SecretAccessed(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.secret.accessed"
    secret_id: str
    secret_name: str


class SecretRotated(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.secret.rotated"
    secret_id: str
    secret_name: str
    new_version: int
    previous_version: int


class SecretExpired(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.secret.expired"
    secret_id: str
    secret_name: str
    expired_at: datetime = Field(default_factory=utc_now)


class KeyGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.key.generated"
    key_id: str
    key_name: str
    algorithm: str
    key_size: int


class KeyRotated(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.key.rotated"
    key_id: str
    key_name: str
    new_key_id: str


class CertificateRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.certificate.registered"
    certificate_id: str
    certificate_name: str


class CertificateExpiring(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.certificate.expiring"
    certificate_id: str
    certificate_name: str
    expires_at: datetime | None = None
    days_remaining: int


class CertificateRevoked(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.certificate.revoked"
    certificate_id: str
    certificate_name: str
    revoked_at: datetime = Field(default_factory=utc_now)


class ComplianceCheckCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.compliance.check_completed"
    framework: str
    report_id: str
    status: str
    score: float | None = None
    control_count: int = 0


class SecurityFindingCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.finding.created"
    finding_id: str
    severity: str
    title: str
    finding_type: str


class FindingStatusChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.security.finding.status_changed"
    finding_id: str
    previous_status: str
    new_status: str
