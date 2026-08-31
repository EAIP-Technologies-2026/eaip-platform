"""Tests for dashboard domain events."""

from __future__ import annotations

from eaip.dashboard.events import (
    DashboardCreated,
    DashboardDeleted,
    DashboardUpdated,
    WidgetAdded,
)
from eaip.events.event import DomainEvent


class TestDashboardCreated:
    def test_event_type(self) -> None:
        event = DashboardCreated(dashboard_id="d1", name="Test")
        assert event.event_type == "eaip.dashboard.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DashboardCreated(dashboard_id="d1", name="Test")
        assert event.dashboard_id == "d1"
        assert event.name == "Test"


class TestDashboardUpdated:
    def test_event_type(self) -> None:
        event = DashboardUpdated(dashboard_id="d1", changes={"name": "New"})
        assert event.event_type == "eaip.dashboard.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DashboardUpdated(dashboard_id="d1", changes={"name": "New"})
        assert event.dashboard_id == "d1"
        assert event.changes == {"name": "New"}


class TestDashboardDeleted:
    def test_event_type(self) -> None:
        event = DashboardDeleted(dashboard_id="d1")
        assert event.event_type == "eaip.dashboard.deleted"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DashboardDeleted(dashboard_id="d1")
        assert event.dashboard_id == "d1"


class TestWidgetAdded:
    def test_event_type(self) -> None:
        event = WidgetAdded(dashboard_id="d1", widget_id="w1", widget_type="chart")
        assert event.event_type == "eaip.dashboard.widget.added"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = WidgetAdded(dashboard_id="d1", widget_id="w1", widget_type="chart")
        assert event.dashboard_id == "d1"
        assert event.widget_id == "w1"
        assert event.widget_type == "chart"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(DashboardCreated, DomainEvent)
        assert issubclass(DashboardUpdated, DomainEvent)
        assert issubclass(DashboardDeleted, DomainEvent)
        assert issubclass(WidgetAdded, DomainEvent)
