"""Tests for queue domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.queue.events import (
    MessageDeadLettered,
    MessageDequeued,
    MessageEnqueued,
    MessageFailed,
    QueueDepthWarning,
)


class TestMessageEnqueued:
    """Tests for MessageEnqueued event."""

    def test_event_type(self) -> None:
        """MessageEnqueued has the correct event type."""
        event = MessageEnqueued(queue_name="q", message_id="m1", content_type="text/plain")
        assert event.event_type == "eaip.queue.message_enqueued"

    def test_is_domain_event(self) -> None:
        """MessageEnqueued is a DomainEvent."""
        event = MessageEnqueued(queue_name="q", message_id="m1", content_type="text/plain")
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        """MessageEnqueued stores all fields."""
        event = MessageEnqueued(
            queue_name="orders", message_id="m1", content_type="application/json"
        )
        assert event.queue_name == "orders"
        assert event.message_id == "m1"
        assert event.content_type == "application/json"


class TestMessageDequeued:
    """Tests for MessageDequeued event."""

    def test_event_type(self) -> None:
        """MessageDequeued has the correct event type."""
        event = MessageDequeued(queue_name="q", message_id="m1", consumer_id="c1")
        assert event.event_type == "eaip.queue.message_dequeued"

    def test_fields(self) -> None:
        """MessageDequeued stores all fields."""
        event = MessageDequeued(queue_name="orders", message_id="m1", consumer_id="consumer-1")
        assert event.consumer_id == "consumer-1"


class TestMessageFailed:
    """Tests for MessageFailed event."""

    def test_event_type(self) -> None:
        """MessageFailed has the correct event type."""
        event = MessageFailed(
            queue_name="q", message_id="m1", error="timeout", retry_count=1, will_retry=True
        )
        assert event.event_type == "eaip.queue.message_failed"

    def test_will_retry_flag(self) -> None:
        """MessageFailed carries the will_retry flag."""
        event = MessageFailed(
            queue_name="q", message_id="m1", error="err", retry_count=2, will_retry=False
        )
        assert event.will_retry is False


class TestMessageDeadLettered:
    """Tests for MessageDeadLettered event."""

    def test_event_type(self) -> None:
        """MessageDeadLettered has the correct event type."""
        event = MessageDeadLettered(queue_name="q", message_id="m1", reason="max retries")
        assert event.event_type == "eaip.queue.message_dead_lettered"

    def test_reason(self) -> None:
        """MessageDeadLettered stores the reason."""
        event = MessageDeadLettered(
            queue_name="orders", message_id="m1", reason="exceeded max retries"
        )
        assert event.reason == "exceeded max retries"


class TestQueueDepthWarning:
    """Tests for QueueDepthWarning event."""

    def test_event_type(self) -> None:
        """QueueDepthWarning has the correct event type."""
        event = QueueDepthWarning(queue_name="q", depth=100, threshold=50)
        assert event.event_type == "eaip.queue.depth_warning"

    def test_depth_and_threshold(self) -> None:
        """QueueDepthWarning stores depth and threshold."""
        event = QueueDepthWarning(queue_name="orders", depth=200, threshold=100)
        assert event.depth == 200
        assert event.threshold == 100
