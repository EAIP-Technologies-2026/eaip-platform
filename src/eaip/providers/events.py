"""Provider domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ProviderRegistered(DomainEvent):
    """Published when a new provider is registered."""

    event_type: ClassVar[str] = "eaip.provider.registered"

    provider_name: str
    provider_type: str
    default_model: str


class ProviderUnregistered(DomainEvent):
    """Published when a provider is removed."""

    event_type: ClassVar[str] = "eaip.provider.unregistered"

    provider_name: str


class ProviderStatusChanged(DomainEvent):
    """Published when a provider's health status changes."""

    event_type: ClassVar[str] = "eaip.provider.status_changed"

    provider_name: str
    previous_status: str
    current_status: str


class ProviderRequestStarted(DomainEvent):
    """Published when a provider request begins."""

    event_type: ClassVar[str] = "eaip.provider.request_started"

    provider_name: str
    model: str
    stream: bool


class ProviderRequestCompleted(DomainEvent):
    """Published when a provider request completes successfully."""

    event_type: ClassVar[str] = "eaip.provider.request_completed"

    provider_name: str
    model: str
    duration_ms: float
    finish_reason: str


class ProviderRequestFailed(DomainEvent):
    """Published when a provider request fails."""

    event_type: ClassVar[str] = "eaip.provider.request_failed"

    provider_name: str
    model: str
    error: str


class ProviderModelDiscovered(DomainEvent):
    """Published when a new model is discovered from a provider."""

    event_type: ClassVar[str] = "eaip.provider.model_discovered"

    provider_name: str
    model_id: str


__all__ = [
    "ProviderModelDiscovered",
    "ProviderRegistered",
    "ProviderRequestCompleted",
    "ProviderRequestFailed",
    "ProviderRequestStarted",
    "ProviderStatusChanged",
    "ProviderUnregistered",
]
