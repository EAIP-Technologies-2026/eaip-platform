"""Tour domain models — state machine, steps, context, fixtures."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TourState(StrEnum):
    """Bounded state machine for the guided tour."""

    IDLE = "idle"
    INTRO = "intro"
    NAVIGATING = "navigating"
    EXPLAINING = "explaining"
    DEMONSTRATING = "demonstrating"
    WAITING = "waiting"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TourCommand(StrEnum):
    """Voice / UI commands the user can issue during a tour."""

    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    NEXT = "next"
    PREVIOUS = "previous"
    SKIP = "skip"
    STOP = "stop"
    REPEAT = "repeat"
    EXPLAIN = "explain"
    EXPLAIN_SIMPLE = "explain_simple"
    WHAT_DOES_THIS_DO = "what_does_this_do"
    GO_TO = "go_to"
    TRY_MYSELF = "try_myself"
    MOST_IMPORTANT = "most_important"


class TourStep(BaseModel):
    """A single deterministic step in the guided tour sequence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    order: int
    route: str
    application: str
    title: str
    narration: str
    why_it_matters: str
    demo_description: str = ""
    demo_fixture_type: str = ""
    demo_safe: bool = True


class TourDemoFixture(BaseModel):
    """A temporary object created for a safe tour demonstration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tour_session_id: str
    fixture_type: str
    name: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    cleaned_up: bool = False


class TourContext(BaseModel):
    """Full contextual state for an active tour session."""

    model_config = ConfigDict(extra="ignore")

    tour_session_id: str
    user_id: str
    tenant_id: str
    current_state: TourState = TourState.IDLE
    current_step_index: int = 0
    current_route: str = "/"
    current_application: str = "enterprise_console"
    theme: str = "light"
    voice_enabled: bool = False
    steps: tuple[TourStep, ...] = ()
    fixtures: tuple[TourDemoFixture, ...] = ()
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class TourRequest(BaseModel):
    """Request body for tour API operations."""

    model_config = ConfigDict(extra="ignore")

    command: TourCommand = TourCommand.START
    step_id: str | None = None
    route: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class TourResponse(BaseModel):
    """Response body for tour API operations."""

    model_config = ConfigDict(extra="forbid")

    tour_session_id: str
    state: TourState
    current_step: TourStep | None = None
    current_step_index: int = 0
    total_steps: int = 0
    narration: str = ""
    route: str = "/"
    application: str = "enterprise_console"
    fixtures: tuple[TourDemoFixture, ...] = ()
    voice_narration: str = ""
    error: str | None = None


__all__ = [
    "TourCommand",
    "TourContext",
    "TourDemoFixture",
    "TourRequest",
    "TourResponse",
    "TourState",
    "TourStep",
]
