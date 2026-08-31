"""Domain events for the secrets distribution service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SecretDistributed(DomainEvent):
    """Emitted when a secret is successfully distributed to a target."""

    event_type: ClassVar[str] = "eaip.secdist.secret.distributed"

    package_id: str
    target_id: str
    name: str


class DistributionFailed(DomainEvent):
    """Emitted when a secret distribution attempt fails."""

    event_type: ClassVar[str] = "eaip.secdist.distribution.failed"

    package_id: str
    target_id: str
    error_message: str


class DistributionRevoked(DomainEvent):
    """Emitted when a previously distributed secret is revoked."""

    event_type: ClassVar[str] = "eaip.secdist.distribution.revoked"

    package_id: str
    target_id: str
    reason: str


__all__ = [
    "DistributionFailed",
    "DistributionRevoked",
    "SecretDistributed",
]
