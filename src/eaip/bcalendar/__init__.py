"""Business Calendar Service — manage events, availability, and working hours."""

from __future__ import annotations

from eaip.bcalendar.events import (
    AvailabilityChecked,
    EventCancelled,
    EventCreated,
    EventUpdated,
)
from eaip.bcalendar.exceptions import (
    CalendarError,
    EventNotFoundError,
)
from eaip.bcalendar.health import CalendarHealthCheck
from eaip.bcalendar.integration import CalendarRuntimeModule
from eaip.bcalendar.models import (
    Availability,
    CalendarConfig,
    CalendarEvent,
    EventStatus,
    WorkingHours,
)
from eaip.bcalendar.service import CalendarService

__all__ = [
    "Availability",
    "AvailabilityChecked",
    "CalendarConfig",
    "CalendarError",
    "CalendarEvent",
    "CalendarHealthCheck",
    "CalendarRuntimeModule",
    "CalendarService",
    "EventCancelled",
    "EventCreated",
    "EventNotFoundError",
    "EventStatus",
    "EventUpdated",
    "WorkingHours",
]
