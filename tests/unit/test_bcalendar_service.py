"""Tests for CalendarService."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest

from eaip.bcalendar.exceptions import CalendarError, EventNotFoundError
from eaip.bcalendar.models import (
    CalendarConfig,
    CalendarEvent,
    EventStatus,
    WorkingHours,
)
from eaip.bcalendar.service import CalendarService


class TestCalendarService:
    @pytest.fixture
    def service(self) -> CalendarService:
        return CalendarService()

    @pytest.fixture
    def sample_event(self) -> CalendarEvent:
        return CalendarEvent(
            id="e1",
            title="Team Meeting",
            start_time=datetime(2025, 6, 1, 10, 0),
            end_time=datetime(2025, 6, 1, 11, 0),
        )

    class TestCreateEvent:
        async def test_create(self, service: CalendarService, sample_event: CalendarEvent) -> None:
            result = await service.create_event(sample_event)
            assert result.id == "e1"
            assert result.title == "Team Meeting"

        async def test_create_invalid_dates(self, service: CalendarService) -> None:
            event = CalendarEvent(
                id="e1",
                title="Bad",
                start_time=datetime(2025, 6, 1, 11, 0),
                end_time=datetime(2025, 6, 1, 10, 0),
            )
            with pytest.raises(CalendarError):
                await service.create_event(event)

    class TestGetEvent:
        async def test_get(self, service: CalendarService, sample_event: CalendarEvent) -> None:
            await service.create_event(sample_event)
            event = await service.get_event("e1")
            assert event.title == "Team Meeting"

        async def test_get_not_found(self, service: CalendarService) -> None:
            with pytest.raises(EventNotFoundError):
                await service.get_event("nonexistent")

    class TestListEvents:
        async def test_list_all(
            self, service: CalendarService, sample_event: CalendarEvent
        ) -> None:
            await service.create_event(sample_event)
            events = await service.list_events()
            assert len(events) == 1

        async def test_list_by_status(
            self, service: CalendarService, sample_event: CalendarEvent
        ) -> None:
            await service.create_event(sample_event)
            events = await service.list_events(status=EventStatus.SCHEDULED)
            assert len(events) == 1
            events = await service.list_events(status=EventStatus.CONFIRMED)
            assert len(events) == 0

    class TestUpdateEvent:
        async def test_update(self, service: CalendarService, sample_event: CalendarEvent) -> None:
            await service.create_event(sample_event)
            updated = await service.update_event("e1", title="Updated Meeting")
            assert updated.title == "Updated Meeting"

        async def test_update_not_found(self, service: CalendarService) -> None:
            with pytest.raises(EventNotFoundError):
                await service.update_event("nonexistent", title="X")

    class TestCancelEvent:
        async def test_cancel(self, service: CalendarService, sample_event: CalendarEvent) -> None:
            await service.create_event(sample_event)
            cancelled = await service.cancel_event("e1", reason="No longer needed")
            assert cancelled.status == EventStatus.CANCELLED

        async def test_cancel_not_found(self, service: CalendarService) -> None:
            with pytest.raises(EventNotFoundError):
                await service.cancel_event("nonexistent")

    class TestCheckAvailability:
        async def test_available(
            self, service: CalendarService, sample_event: CalendarEvent
        ) -> None:
            await service.create_event(sample_event)
            availability = await service.check_availability(date(2025, 6, 2))
            assert availability.available is True
            assert len(availability.slots) > 0

        async def test_not_available(self, service: CalendarService) -> None:
            event = CalendarEvent(
                id="e1",
                title="All Day",
                start_time=datetime(2025, 6, 1, 0, 0),
                end_time=datetime(2025, 6, 1, 23, 59),
            )
            await service.create_event(event)
            availability = await service.check_availability(date(2025, 6, 1))
            assert availability.available is False

    class TestWorkingHours:
        async def test_get_default_hours(self, service: CalendarService) -> None:
            hours = await service.get_working_hours(0)
            assert hours.start_time == time(9, 0)
            assert hours.end_time == time(17, 0)

        async def test_set_working_hours(self, service: CalendarService) -> None:
            wh = WorkingHours(day_of_week=1, start_time=time(8, 0), end_time=time(18, 0))
            result = await service.set_working_hours(wh)
            assert result.start_time == time(8, 0)
            assert result.end_time == time(18, 0)
            fetched = await service.get_working_hours(1)
            assert fetched.start_time == time(8, 0)

    class TestConfig:
        def test_default_config(self) -> None:
            s = CalendarService()
            assert s.config.default_event_duration_minutes == 60
            assert s.config.max_attendees == 100

        def test_custom_config(self) -> None:
            config = CalendarConfig(default_event_duration_minutes=30, max_attendees=50)
            s = CalendarService(config=config)
            assert s.config.default_event_duration_minutes == 30
            assert s.config.max_attendees == 50
