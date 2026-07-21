"""Tests for webhook models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.webhooks.models import (
    DeliveryReceipt,
    DeliveryStatus,
    EndpointStatus,
    WebhookConfig,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookSecret,
)


class TestWebhookEndpoint:
    def test_minimal(self) -> None:
        ep = WebhookEndpoint(id="ep1", name="My Hook", url="https://example.com/hook")
        assert ep.status == EndpointStatus.ACTIVE
        assert ep.enabled is True
        assert ep.events == ()
        assert ep.timeout_seconds == 30

    def test_frozen(self) -> None:
        ep = WebhookEndpoint(id="ep1", name="My Hook", url="https://example.com/hook")
        with pytest.raises(ValidationError):
            ep.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WebhookEndpoint(id="ep1", name="N", url="https://example.com/hook", unknown=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        ep = WebhookEndpoint(
            id="ep1",
            name="Full Hook",
            url="https://example.com/hook",
            secret="s3cr3t",
            events=("order.created", "order.updated"),
            headers={"Authorization": "Bearer token"},
            retry_config={"max_attempts": 5},
            timeout_seconds=60,
            rate_limit_per_minute=120,
            enabled=False,
            status=EndpointStatus.PAUSED,
            created_at=ts,
            updated_at=ts,
            metadata={"owner": "team-a"},
        )
        assert ep.secret == "s3cr3t"
        assert ep.events == ("order.created", "order.updated")
        assert ep.headers == {"Authorization": "Bearer token"}
        assert ep.retry_config == {"max_attempts": 5}
        assert ep.timeout_seconds == 60
        assert ep.rate_limit_per_minute == 120
        assert ep.enabled is False
        assert ep.status == EndpointStatus.PAUSED
        assert ep.metadata == {"owner": "team-a"}

    def test_all_statuses(self) -> None:
        for st in EndpointStatus:
            ep = WebhookEndpoint(id="ep1", name="N", url="https://example.com/hook", status=st)
            assert ep.status == st


class TestWebhookDelivery:
    def test_minimal(self) -> None:
        d = WebhookDelivery(id="d1", endpoint_id="ep1", event_type="order.created")
        assert d.status == DeliveryStatus.PENDING
        assert d.attempt == 1
        assert d.max_attempts == 3

    def test_frozen(self) -> None:
        d = WebhookDelivery(id="d1", endpoint_id="ep1", event_type="order.created")
        with pytest.raises(ValidationError):
            d.status = DeliveryStatus.DELIVERED

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WebhookDelivery(id="d1", endpoint_id="ep1", event_type="order.created", unknown=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        d = WebhookDelivery(
            id="d1",
            endpoint_id="ep1",
            event_type="order.created",
            payload={"order_id": "123"},
            status=DeliveryStatus.FAILED,
            attempt=3,
            max_attempts=5,
            last_attempt_at=ts,
            delivered_at=ts,
            response_status_code=500,
            response_body="Internal error",
            duration_ms=1500.0,
            error="timeout",
            next_retry_at=ts,
            metadata={"env": "prod"},
        )
        assert d.payload == {"order_id": "123"}
        assert d.status == DeliveryStatus.FAILED
        assert d.attempt == 3
        assert d.max_attempts == 5
        assert d.response_status_code == 500
        assert d.duration_ms == 1500.0
        assert d.error == "timeout"

    def test_all_statuses(self) -> None:
        for st in DeliveryStatus:
            d = WebhookDelivery(id="d1", endpoint_id="ep1", event_type="t", status=st)
            assert d.status == st


class TestWebhookSecret:
    def test_minimal(self) -> None:
        s = WebhookSecret(id="s1", endpoint_id="ep1", key="abc123")
        assert s.version == 1
        assert s.active is True

    def test_frozen(self) -> None:
        s = WebhookSecret(id="s1", endpoint_id="ep1", key="abc")
        with pytest.raises(ValidationError):
            s.key = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WebhookSecret(id="s1", endpoint_id="ep1", key="abc", unknown=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        s = WebhookSecret(
            id="s1",
            endpoint_id="ep1",
            key="key-123",
            version=3,
            created_at=ts,
            expires_at=ts,
            active=False,
            metadata={"rotated_by": "admin"},
        )
        assert s.version == 3
        assert s.expires_at == ts
        assert s.active is False
        assert s.metadata == {"rotated_by": "admin"}


class TestDeliveryReceipt:
    def test_minimal(self) -> None:
        r = DeliveryReceipt(
            id="r1", delivery_id="d1", endpoint_id="ep1", status=DeliveryStatus.DELIVERED
        )
        assert r.checksum == ""

    def test_frozen(self) -> None:
        r = DeliveryReceipt(
            id="r1", delivery_id="d1", endpoint_id="ep1", status=DeliveryStatus.DELIVERED
        )
        with pytest.raises(ValidationError):
            r.status = DeliveryStatus.FAILED

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DeliveryReceipt(
                id="r1",
                delivery_id="d1",
                endpoint_id="ep1",
                status=DeliveryStatus.DELIVERED,
                unknown=True,
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        r = DeliveryReceipt(
            id="r1",
            delivery_id="d1",
            endpoint_id="ep1",
            status=DeliveryStatus.DELIVERED,
            timestamp=ts,
            headers_sent={"X-Signature-256": "abc"},
            response_summary={"status_code": 200},
            checksum="sha256-check",
            metadata={"version": "1"},
        )
        assert r.headers_sent == {"X-Signature-256": "abc"}
        assert r.response_summary == {"status_code": 200}
        assert r.checksum == "sha256-check"


class TestWebhookConfig:
    def test_defaults(self) -> None:
        c = WebhookConfig()
        assert c.default_max_attempts == 3
        assert c.default_retry_delay_seconds == 60
        assert c.backoff_multiplier == 2.0
        assert c.max_backoff_seconds == 3600
        assert c.signature_header_name == "X-Signature-256"
        assert c.default_timeout_seconds == 30
        assert c.max_concurrent_deliveries == 10
        assert c.delivery_retention_days == 30
        assert c.enable_delivery_tracking is True

    def test_custom(self) -> None:
        c = WebhookConfig(
            default_max_attempts=5,
            default_retry_delay_seconds=120,
            backoff_multiplier=3.0,
            max_backoff_seconds=7200,
            signature_header_name="X-Custom-Sig",
            default_timeout_seconds=60,
            max_concurrent_deliveries=20,
            delivery_retention_days=90,
            enable_delivery_tracking=False,
        )
        assert c.default_max_attempts == 5
        assert c.default_retry_delay_seconds == 120
        assert c.backoff_multiplier == 3.0
        assert c.max_backoff_seconds == 7200
        assert c.signature_header_name == "X-Custom-Sig"
        assert c.default_timeout_seconds == 60
        assert c.max_concurrent_deliveries == 20
        assert c.delivery_retention_days == 90
        assert c.enable_delivery_tracking is False

    def test_frozen(self) -> None:
        c = WebhookConfig()
        with pytest.raises(ValidationError):
            c.default_max_attempts = 10

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WebhookConfig(unknown=True)
