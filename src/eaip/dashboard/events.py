"""Domain events for the custom dashboard builder."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class DashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.dashboard.created"

    dashboard_id: str
    name: str


class DashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.dashboard.updated"

    dashboard_id: str
    changes: dict[str, Any]


class DashboardDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.dashboard.deleted"

    dashboard_id: str


class WidgetAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.dashboard.widget.added"

    dashboard_id: str
    widget_id: str
    widget_type: str


__all__ = [
    "DashboardCreated",
    "DashboardDeleted",
    "DashboardUpdated",
    "WidgetAdded",
]
