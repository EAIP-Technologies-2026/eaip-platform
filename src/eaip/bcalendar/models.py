"""Data models for the business calendar service."""

from __future__ import annotations

from datetime import datetime, time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EventStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CalendarEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    description: str = Field(default="")
    start_time: datetime
    end_time: datetime
    status: EventStatus = Field(default=EventStatus.SCHEDULED)
    location: str = Field(default="")
    attendees: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Availability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    date: str
    available: bool = Field(default=True)
    slots: tuple[tuple[str, str], ...] = Field(default=())


class WorkingHours(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    day_of_week: int = Field(default=0, ge=0, le=6)
    start_time: time = Field(default=time(9, 0))
    end_time: time = Field(default=time(17, 0))


class CalendarConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_event_duration_minutes: int = Field(default=60, ge=15)
    max_attendees: int = Field(default=100, ge=1)


__all__ = [
    "Availability",
    "CalendarConfig",
    "CalendarEvent",
    "EventStatus",
    "WorkingHours",
]
