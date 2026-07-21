"""Tests for metering domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.metering.events import (
    AggregateComputed,
    UsageRecorded,
    UsageThresholdReached,
)


class TestUsageRecorded:
    def test_event_type(self) -> None:
        event = UsageRecorded(
            record_id="r1", tenant_id="t1", metric_name="api_calls", metric_value=100.0
        )
        assert event.event_type == "eaip.metering.usage.recorded"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = UsageRecorded(
            record_id="r1", tenant_id="t1", metric_name="api_calls", metric_value=100.0
        )
        assert event.record_id == "r1"
        assert event.tenant_id == "t1"
        assert event.metric_name == "api_calls"
        assert event.metric_value == 100.0


class TestUsageThresholdReached:
    def test_event_type(self) -> None:
        event = UsageThresholdReached(
            tenant_id="t1", metric_name="api_calls", current_value=90.0, threshold=80.0
        )
        assert event.event_type == "eaip.metering.usage.threshold_reached"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = UsageThresholdReached(
            tenant_id="t1", metric_name="api_calls", current_value=90.0, threshold=80.0
        )
        assert event.tenant_id == "t1"
        assert event.current_value == 90.0
        assert event.threshold == 80.0


class TestAggregateComputed:
    def test_event_type(self) -> None:
        event = AggregateComputed(
            metric_name="api_calls", tenant_id="t1", period="daily", total_value=500.0
        )
        assert event.event_type == "eaip.metering.aggregate.computed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AggregateComputed(
            metric_name="api_calls", tenant_id="t1", period="daily", total_value=500.0
        )
        assert event.metric_name == "api_calls"
        assert event.total_value == 500.0
        assert event.period == "daily"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(UsageRecorded, DomainEvent)
        assert issubclass(UsageThresholdReached, DomainEvent)
        assert issubclass(AggregateComputed, DomainEvent)
