"""Domain events for capability lifecycle transitions."""

from __future__ import annotations

from eaip.events.event import DomainEvent


class CapabilityRegistered(DomainEvent):
    """Emitted when a capability is first registered."""

    name: str
    version: str
    contract_version: str | None = None


class CapabilityEnabled(DomainEvent):
    """Emitted when a capability transitions to ENABLED."""

    name: str
    version: str


class CapabilityDisabled(DomainEvent):
    """Emitted when a capability transitions to DISABLED."""

    name: str
    version: str


class CapabilityDeprecated(DomainEvent):
    """Emitted when a capability is marked DEPRECATED."""

    name: str
    version: str


class CapabilityUpgraded(DomainEvent):
    """Emitted when a capability's version changes via replace."""

    name: str
    previous_version: str
    new_version: str


class CapabilityHealthChanged(DomainEvent):
    """Emitted when a capability's health status changes."""

    name: str
    status: str
    message: str


__all__ = [
    "CapabilityDeprecated",
    "CapabilityDisabled",
    "CapabilityEnabled",
    "CapabilityHealthChanged",
    "CapabilityRegistered",
    "CapabilityUpgraded",
]
