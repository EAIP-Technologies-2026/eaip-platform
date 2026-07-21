"""Tests for webhook domain events."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.events.event import DomainEvent
from eaip.webhooks.events import (
    EndpointRegistered,
    EndpointUpdated,
    SecretExpired,
    SecretRotated,
    WebhookDelivered,
    WebhookDeliveryConfirmed,
    WebhookDeliveryFailed,
    WebhookRetrying,
)


class TestEndpointRegistered:
    def test_event_type(self) -> None:
        event = EndpointRegistered(
            endpoint_id="ep1", name="My Hook", url="https://example.com/hook"
        )
        assert event.event_type == "webhook.endpoint.registered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EndpointRegistered(
            endpoint_id="ep1", name="My Hook", url="https://example.com/hook"
        )
        assert event.endpoint_id == "ep1"
        assert event.name == "My Hook"
        assert event.url == "https://example.com/hook"


class TestEndpointUpdated:
    def test_event_type(self) -> None:
        event = EndpointUpdated(endpoint_id="ep1", name="Updated", url="https://example.com/v2")
        assert event.event_type == "webhook.endpoint.updated"

    def test_fields(self) -> None:
        event = EndpointUpdated(endpoint_id="ep1", name="Updated", url="https://example.com/v2")
        assert event.name == "Updated"


class TestWebhookDelivered:
    def test_event_type(self) -> None:
        event = WebhookDelivered(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            status_code=200,
            duration_ms=150.0,
        )
        assert event.event_type == "webhook.delivered"

    def test_fields(self) -> None:
        event = WebhookDelivered(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            status_code=200,
            duration_ms=150.0,
        )
        assert event.status_code == 200
        assert event.duration_ms == 150.0


class TestWebhookDeliveryFailed:
    def test_event_type(self) -> None:
        event = WebhookDeliveryFailed(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            error="timeout",
            attempt=3,
        )
        assert event.event_type == "webhook.delivery.failed"

    def test_fields(self) -> None:
        event = WebhookDeliveryFailed(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            error="timeout",
            attempt=3,
        )
        assert event.error == "timeout"
        assert event.attempt == 3


class TestWebhookRetrying:
    def test_event_type(self) -> None:
        ts = datetime.now(UTC)
        event = WebhookRetrying(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            attempt=2,
            next_retry_at=ts,
        )
        assert event.event_type == "webhook.delivery.retrying"

    def test_fields(self) -> None:
        ts = datetime.now(UTC)
        event = WebhookRetrying(
            delivery_id="d1",
            endpoint_id="ep1",
            event_type_name="order.created",
            attempt=2,
            next_retry_at=ts,
        )
        assert event.attempt == 2
        assert event.next_retry_at == ts


class TestWebhookDeliveryConfirmed:
    def test_event_type(self) -> None:
        ts = datetime.now(UTC)
        event = WebhookDeliveryConfirmed(
            delivery_id="d1", endpoint_id="ep1", checksum="abc", timestamp=ts
        )
        assert event.event_type == "webhook.delivery.confirmed"

    def test_fields(self) -> None:
        ts = datetime.now(UTC)
        event = WebhookDeliveryConfirmed(
            delivery_id="d1", endpoint_id="ep1", checksum="abc", timestamp=ts
        )
        assert event.checksum == "abc"
        assert event.timestamp == ts


class TestSecretRotated:
    def test_event_type(self) -> None:
        event = SecretRotated(endpoint_id="ep1", old_version=1, new_version=2)
        assert event.event_type == "webhook.secret.rotated"

    def test_fields(self) -> None:
        event = SecretRotated(endpoint_id="ep1", old_version=1, new_version=2)
        assert event.old_version == 1
        assert event.new_version == 2


class TestSecretExpired:
    def test_event_type(self) -> None:
        event = SecretExpired(endpoint_id="ep1", secret_id="s1", version=3)
        assert event.event_type == "webhook.secret.expired"

    def test_fields(self) -> None:
        event = SecretExpired(endpoint_id="ep1", secret_id="s1", version=3)
        assert event.secret_id == "s1"
        assert event.version == 3


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(EndpointRegistered, DomainEvent)
        assert issubclass(EndpointUpdated, DomainEvent)
        assert issubclass(WebhookDelivered, DomainEvent)
        assert issubclass(WebhookDeliveryFailed, DomainEvent)
        assert issubclass(WebhookRetrying, DomainEvent)
        assert issubclass(WebhookDeliveryConfirmed, DomainEvent)
        assert issubclass(SecretRotated, DomainEvent)
        assert issubclass(SecretExpired, DomainEvent)
