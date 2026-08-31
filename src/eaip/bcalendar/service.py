"""CalendarService — manage events, availability, and working hours."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from eaip.bcalendar.events import (
    AvailabilityChecked,
    EventCancelled,
    EventCreated,
    EventUpdated,
)
from eaip.bcalendar.exceptions import CalendarError, EventNotFoundError
from eaip.bcalendar.models import (
    Availability,
    CalendarConfig,
    CalendarEvent,
    EventStatus,
    WorkingHours,
)
from eaip.logging.context import get_logger


class CalendarService:
    def __init__(self, config: CalendarConfig | None = None) -> None:
        self._config = config or CalendarConfig()
        self._events: dict[str, CalendarEvent] = {}
        self._working_hours: dict[int, WorkingHours] = {}
        self._log = get_logger("eaip.bcalendar.service")

    @property
    def config(self) -> CalendarConfig:
        return self._config

    async def create_event(self, event: CalendarEvent) -> CalendarEvent:
        if event.end_time <= event.start_time:
            raise CalendarError("End time must be after start time")
        self._events[event.id] = event
        EventCreated(event_id=event.id, title=event.title)
        self._log.info("bcalendar.event.created", event_id=event.id, title=event.title)
        return event

    async def get_event(self, event_id: str) -> CalendarEvent:
        event = self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Event '{event_id}' not found")
        return event

    async def list_events(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        status: EventStatus | None = None,
    ) -> list[CalendarEvent]:
        results: list[CalendarEvent] = []
        for event in self._events.values():
            if status is not None and event.status != status:
                continue
            if start_date is not None and event.start_time.date() < start_date:
                continue
            if end_date is not None and event.end_time.date() > end_date:
                continue
            results.append(event)
        results.sort(key=lambda e: e.start_time)
        return results

    async def update_event(self, event_id: str, **updates: str) -> CalendarEvent:
        event = await self.get_event(event_id)
        if "status" in updates and updates["status"] == EventStatus.CANCELLED.value:
            updated = event.model_copy(update={"status": EventStatus.CANCELLED}, deep=True)
        else:
            updated = event.model_copy(update=updates, deep=True)
        self._events[event_id] = updated
        EventUpdated(event_id=event_id, changes=updates)
        self._log.info("bcalendar.event.updated", event_id=event_id)
        return updated

    async def cancel_event(self, event_id: str, reason: str = "") -> CalendarEvent:
        event = await self.get_event(event_id)
        updated = event.model_copy(update={"status": EventStatus.CANCELLED}, deep=True)
        self._events[event_id] = updated
        EventCancelled(event_id=event_id, reason=reason)
        self._log.info("bcalendar.event.cancelled", event_id=event_id, reason=reason)
        return updated

    async def check_availability(self, check_date: date) -> Availability:
        day_of_week = check_date.weekday()
        wh = self._working_hours.get(day_of_week)
        if wh is None:
            wh = WorkingHours(day_of_week=day_of_week)

        slots: list[tuple[str, str]] = []
        slot_start = datetime.combine(check_date, wh.start_time)
        slot_end = datetime.combine(check_date, wh.end_time)
        duration = timedelta(minutes=self._config.default_event_duration_minutes)

        current = slot_start
        while current + duration <= slot_end:
            conflict = False
            for event in self._events.values():
                if event.status in (EventStatus.CANCELLED, EventStatus.COMPLETED):
                    continue
                if event.start_time < current + duration and event.end_time > current:
                    conflict = True
                    break
            if not conflict:
                slots.append((current.isoformat(), (current + duration).isoformat()))
            current += duration

        available = len(slots) > 0
        result = Availability(date=check_date.isoformat(), available=available, slots=tuple(slots))
        AvailabilityChecked(date=check_date.isoformat(), available=available)
        return result

    async def get_working_hours(self, day_of_week: int) -> WorkingHours:
        return self._working_hours.get(day_of_week, WorkingHours(day_of_week=day_of_week))

    async def set_working_hours(self, hours: WorkingHours) -> WorkingHours:
        self._working_hours[hours.day_of_week] = hours
        self._log.info(
            "bcalendar.working_hours.set",
            day_of_week=hours.day_of_week,
            start=hours.start_time.isoformat(),
            end=hours.end_time.isoformat(),
        )
        return hours


__all__ = ["CalendarService"]
