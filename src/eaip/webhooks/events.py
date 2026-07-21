"""Domain events for the webhook dispatcher."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class EndpointRegistered(DomainEvent):
    event_type: ClassVar[str] = "webhook.endpoint.registered"
    endpoint_id: str
    name: str
    url: str


class EndpointUpdated(DomainEvent):
    event_type: ClassVar[str] = "webhook.endpoint.updated"
    endpoint_id: str
    name: str
    url: str


class WebhookDelivered(DomainEvent):
    event_type: ClassVar[str] = "webhook.delivered"
    delivery_id: str
    endpoint_id: str
    event_type_name: str
    status_code: int
    duration_ms: float


class WebhookDeliveryFailed(DomainEvent):
    event_type: ClassVar[str] = "webhook.delivery.failed"
    delivery_id: str
    endpoint_id: str
    event_type_name: str
    error: str
    attempt: int


class WebhookRetrying(DomainEvent):
    event_type: ClassVar[str] = "webhook.delivery.retrying"
    delivery_id: str
    endpoint_id: str
    event_type_name: str
    attempt: int
    next_retry_at: datetime


class WebhookDeliveryConfirmed(DomainEvent):
    event_type: ClassVar[str] = "webhook.delivery.confirmed"
    delivery_id: str
    endpoint_id: str
    checksum: str
    timestamp: datetime


class SecretRotated(DomainEvent):
    event_type: ClassVar[str] = "webhook.secret.rotated"
    endpoint_id: str
    old_version: int
    new_version: int


class SecretExpired(DomainEvent):
    event_type: ClassVar[str] = "webhook.secret.expired"
    endpoint_id: str
    secret_id: str
    version: int


__all__ = [
    "EndpointRegistered",
    "EndpointUpdated",
    "SecretExpired",
    "SecretRotated",
    "WebhookDelivered",
    "WebhookDeliveryConfirmed",
    "WebhookDeliveryFailed",
    "WebhookRetrying",
]
