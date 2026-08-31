"""Domain events for floating license management."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class LicenseCheckedOut(DomainEvent):
    event_type: ClassVar[str] = "eaip.floatlicense.checked_out"

    pool_id: str
    lease_id: str
    licensee: str


class LicenseCheckedIn(DomainEvent):
    event_type: ClassVar[str] = "eaip.floatlicense.checked_in"

    pool_id: str
    lease_id: str
    licensee: str
    checked_in_at: datetime


class LicenseExhausted(DomainEvent):
    event_type: ClassVar[str] = "eaip.floatlicense.exhausted"

    pool_id: str
    name: str
    vendor: str
    product: str
    attempted_licensee: str = Field(default="")


__all__ = [
    "LicenseCheckedIn",
    "LicenseCheckedOut",
    "LicenseExhausted",
]
