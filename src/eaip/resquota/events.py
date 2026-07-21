"""Domain events for resource quotas."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class QuotaExceeded(DomainEvent):
    """Emitted when a quota limit is exceeded."""

    event_type: ClassVar[str] = "eaip.resquota.quota.exceeded"

    quota_id: str
    consumer_id: str
    requested: float
    limit: float


class QuotaAllocated(DomainEvent):
    """Emitted when quota is allocated to a consumer."""

    event_type: ClassVar[str] = "eaip.resquota.quota.allocated"

    quota_id: str
    consumer_id: str
    amount: float


class QuotaReleased(DomainEvent):
    """Emitted when quota is released by a consumer."""

    event_type: ClassVar[str] = "eaip.resquota.quota.released"

    quota_id: str
    consumer_id: str
    amount: float


class QuotaWarning(DomainEvent):
    """Emitted when quota usage reaches the warning threshold."""

    event_type: ClassVar[str] = "eaip.resquota.quota.warning"

    quota_id: str
    consumer_id: str
    usage_percentage: float


__all__ = [
    "QuotaAllocated",
    "QuotaExceeded",
    "QuotaReleased",
    "QuotaWarning",
]
