"""Domain events for license & entitlement management."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class LicenseCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.created"

    license_id: str
    name: str
    key: str
    license_type: str
    features: tuple[str, ...] = Field(default=())


class LicenseActivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.activated"

    license_id: str
    key: str


class LicenseExpired(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.expired"

    license_id: str
    key: str
    expired_at: str


class LicenseRevoked(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.revoked"

    license_id: str
    key: str
    reason: str = Field(default="")


class LicenseSuspended(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.suspended"

    license_id: str
    key: str
    reason: str = Field(default="")


class LicenseValidated(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.validated"

    license_id: str
    key: str
    valid: bool
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())


class FeatureAccessGranted(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.feature.granted"

    license_id: str
    feature_key: str


class FeatureAccessDenied(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.feature.denied"

    license_id: str
    feature_key: str
    reason: str = Field(default="")


class UsageRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.usage.recorded"

    license_id: str
    feature_key: str
    metric: str
    quantity: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuotaWarning(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.quota.warning"

    license_id: str
    resource_type: str
    current: int
    max: int
    usage_percent: float


class QuotaExceeded(DomainEvent):
    event_type: ClassVar[str] = "eaip.license.quota.exceeded"

    license_id: str
    resource_type: str
    current: int
    max: int
    requested: int


__all__ = [
    "FeatureAccessDenied",
    "FeatureAccessGranted",
    "LicenseActivated",
    "LicenseCreated",
    "LicenseExpired",
    "LicenseRevoked",
    "LicenseSuspended",
    "LicenseValidated",
    "QuotaExceeded",
    "QuotaWarning",
    "UsageRecorded",
]
