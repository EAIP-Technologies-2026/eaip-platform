"""Tests for EventEnvelope."""

from __future__ import annotations

import pytest

from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.shared.identifiers import CorrelationId


class OrderPlaced(DomainEvent):
    event_type = "order.placed"
    order_id: str


class TestEventEnvelope:
    def test_from_event_creates_envelope(self):
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        assert envelope.event_type == "order.placed"
        assert envelope.payload["order_id"] == "ord-001"
        assert envelope.event_id is not None
        assert envelope.correlation_id is not None

    def test_from_event_preserves_correlation(self):
        cid = CorrelationId.parse("test-corr-123")
        event = OrderPlaced(order_id="ord-001", correlation_id=cid)
        envelope = EventEnvelope.from_event(event)

        assert envelope.correlation_id == "test-corr-123"

    def test_from_event_accepts_causation_id(self):
        event = OrderPlaced(order_id="ord-001")

        envelope = EventEnvelope.from_event(event, causation_id="cause-456")
        assert envelope.causation_id == "cause-456"

    def test_from_event_accepts_metadata(self):
        event = OrderPlaced(order_id="ord-001")

        envelope = EventEnvelope.from_event(event, metadata={"source": "test"})
        assert envelope.metadata == {"source": "test"}

    def test_envelope_is_frozen(self):
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        with pytest.raises((ValueError, TypeError)):
            envelope.event_id = "changed"  # type: ignore[misc]

    def test_envelope_default_retry_count_zero(self):
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        assert envelope.retry_count == 0
