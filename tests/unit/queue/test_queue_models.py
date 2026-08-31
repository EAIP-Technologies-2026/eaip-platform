"""Tests for queue Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.queue.models import QueueConfig, QueueMessage, QueueStats, QueueSubscription


class TestQueueMessage:
    """Tests for QueueMessage model."""

    def test_create_minimal(self) -> None:
        """A QueueMessage can be created with just message_id and payload."""
        msg = QueueMessage(message_id="m1", payload=b"hello")
        assert msg.message_id == "m1"
        assert msg.payload == b"hello"
        assert msg.content_type == "application/octet-stream"
        assert msg.correlation_id is None
        assert msg.headers == {}
        assert isinstance(msg.created_at, datetime)
        assert msg.retry_count == 0
        assert msg.max_retries == 3

    def test_create_full(self) -> None:
        """A QueueMessage can be created with all fields."""
        now = datetime.now(UTC)
        msg = QueueMessage(
            message_id="m2",
            payload=b"world",
            content_type="text/plain",
            correlation_id="corr-123",
            headers={"source": "test"},
            created_at=now,
            retry_count=1,
            max_retries=5,
        )
        assert msg.message_id == "m2"
        assert msg.correlation_id == "corr-123"
        assert msg.retry_count == 1
        assert msg.max_retries == 5

    def test_extra_fields_forbidden(self) -> None:
        """Extra fields are rejected by the model."""
        with pytest.raises(ValidationError):
            QueueMessage(message_id="m1", payload=b"x", unknown="field")  # type: ignore[call-arg]

    def test_frozen(self) -> None:
        """QueueMessage instances are immutable."""
        msg = QueueMessage(message_id="m1", payload=b"x")
        with pytest.raises(ValidationError):
            msg.message_id = "changed"  # type: ignore[misc]


class TestQueueConfig:
    """Tests for QueueConfig model."""

    def test_create_minimal(self) -> None:
        """A QueueConfig can be created with just a name."""
        config = QueueConfig(name="test-queue")
        assert config.name == "test-queue"
        assert config.max_size == 10000
        assert config.visibility_timeout_seconds == 30
        assert config.delivery_delay_seconds == 0
        assert config.dead_letter_queue is None
        assert config.max_receive_count == 3

    def test_create_full(self) -> None:
        """A QueueConfig can be created with all fields."""
        config = QueueConfig(
            name="orders",
            max_size=500,
            visibility_timeout_seconds=60,
            delivery_delay_seconds=5,
            dead_letter_queue="orders-dlq",
            max_receive_count=5,
        )
        assert config.name == "orders"
        assert config.max_size == 500
        assert config.dead_letter_queue == "orders-dlq"

    def test_extra_fields_forbidden(self) -> None:
        """Extra fields are rejected by the model."""
        with pytest.raises(ValidationError):
            QueueConfig(name="q", extra="x")  # type: ignore[call-arg]

    def test_frozen(self) -> None:
        """QueueConfig instances are immutable."""
        config = QueueConfig(name="q")
        with pytest.raises(ValidationError):
            config.name = "changed"  # type: ignore[misc]


class TestQueueStats:
    """Tests for QueueStats model."""

    def test_create_defaults(self) -> None:
        """QueueStats can be created with default values."""
        stats = QueueStats()
        assert stats.total_enqueued == 0
        assert stats.total_dequeued == 0
        assert stats.total_failed == 0
        assert stats.current_depth == 0
        assert stats.dead_letter_depth == 0

    def test_create_custom(self) -> None:
        """QueueStats can be created with custom values."""
        stats = QueueStats(
            total_enqueued=100,
            total_dequeued=80,
            total_failed=5,
            current_depth=20,
            dead_letter_depth=3,
        )
        assert stats.total_enqueued == 100
        assert stats.dead_letter_depth == 3


class TestQueueSubscription:
    """Tests for QueueSubscription model."""

    def test_create_minimal(self) -> None:
        """A QueueSubscription can be created with required fields."""
        sub = QueueSubscription(
            subscription_id="s1",
            queue_name="q",
            handler_type="default",
        )
        assert sub.subscription_id == "s1"
        assert sub.filter_pattern is None
        assert sub.active is True

    def test_create_with_filter(self) -> None:
        """A QueueSubscription can include a filter pattern."""
        sub = QueueSubscription(
            subscription_id="s2",
            queue_name="orders",
            handler_type="order_processor",
            filter_pattern="type:order.created",
        )
        assert sub.filter_pattern == "type:order.created"

    def test_inactive(self) -> None:
        """A QueueSubscription can be created as inactive."""
        sub = QueueSubscription(
            subscription_id="s3",
            queue_name="q",
            handler_type="h",
            active=False,
        )
        assert sub.active is False
