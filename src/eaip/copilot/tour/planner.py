"""Tour-aware intent routing for the Conductor planner.

When TOUR_MODE is active, the planner intercepts tour-related voice commands
and routes them to the tour service instead of the default Conductor flow.
The normal Conductor planner handles all non-tour messages.
"""

from __future__ import annotations

import re
from typing import Any

from eaip.copilot.planner import ConductorPlanner, Plan
from eaip.copilot.tour.models import TourCommand

# Mapping of natural language patterns to tour commands.
_TOUR_COMMAND_PATTERNS: list[tuple[re.Pattern[str], TourCommand]] = [
    (
        re.compile(r"\b(pause|hold)\b.*\b(tour|guide)\b", re.I),
        TourCommand.PAUSE,
    ),
    (
        re.compile(r"\b(resume|continue|unpause|go on)\b", re.I),
        TourCommand.RESUME,
    ),
    (
        re.compile(r"\b(skip|next)\b.*\b(this|step|section)\b", re.I),
        TourCommand.SKIP,
    ),
    (
        re.compile(r"\b(skip to)\b\s+(.+)", re.I),
        TourCommand.GO_TO,
    ),
    (
        re.compile(r"\b(go back|previous)\b", re.I),
        TourCommand.PREVIOUS,
    ),
    (
        re.compile(r"\b(stop|end)\b.*\b(tour|guide)\b", re.I),
        TourCommand.STOP,
    ),
    (
        re.compile(r"\b(repeat|say again|again)\b", re.I),
        TourCommand.REPEAT,
    ),
    (
        re.compile(r"\b(explain)\b.*\b(that|this|more)\b", re.I),
        TourCommand.EXPLAIN,
    ),
    (
        re.compile(r"\b(explain)\b.*\b(simpler|simple|easier)\b", re.I),
        TourCommand.EXPLAIN_SIMPLE,
    ),
    (
        re.compile(r"\b(what does this (page|screen|do))\b", re.I),
        TourCommand.WHAT_DOES_THIS_DO,
    ),
    (
        re.compile(
            r"\b(show me)\b.*\b"
            r"(agents?|marketplace|knowledge|missions?|monitoring)\b",
            re.I,
        ),
        TourCommand.GO_TO,
    ),
    (
        re.compile(r"\b(can i try|let me try|try myself|hands.?on)\b", re.I),
        TourCommand.TRY_MYSELF,
    ),
    (
        re.compile(r"\b(most important|key thing)\b", re.I),
        TourCommand.MOST_IMPORTANT,
    ),
    (
        re.compile(r"\b(start|begin)\b.*\b(tour|guide)\b", re.I),
        TourCommand.START,
    ),
]

# Map common names to step ids for go_to navigation.
_STEP_ID_MAP: dict[str, str] = {
    "dashboard": "dashboard",
    "agents": "agents",
    "agent": "agents",
    "brains": "brains",
    "brain": "brains",
    "knowledge": "knowledge",
    "missions": "missions",
    "mission": "missions",
    "monitoring": "monitoring",
    "activity": "activity",
    "administration": "administration",
    "admin": "administration",
    "marketplace": "marketplace",
    "memory": "memory",
    "system twin": "system-twin",
    "twin": "system-twin",
    "conductor": "conductor",
    "personal assistant": "conductor",
}

_GO_TO_GROUP_INDEX = 2


class TourPlanner:
    """Route tour-related voice commands during an active tour session.

    This wraps the existing ConductorPlanner.  Tour commands are intercepted;
    all other messages pass through to the underlying planner unchanged.
    """

    def __init__(self, base_planner: ConductorPlanner) -> None:
        """Initialize with the base Conductor planner."""
        self._base = base_planner

    def plan_tour_command(self, message: str) -> tuple[TourCommand, dict[str, Any]] | None:
        """Try to parse the message as a tour command.

        Args:
            message: The raw user message.

        Returns:
            A tuple of (command, context) if matched, None otherwise.
        """
        text = message.strip()
        if not text:
            return None

        for pattern, command in _TOUR_COMMAND_PATTERNS:
            match = pattern.search(text)
            if match:
                context: dict[str, Any] = {}
                if (
                    command is TourCommand.GO_TO
                    and match.lastindex
                    and match.lastindex >= _GO_TO_GROUP_INDEX
                ):
                    target = match.group(_GO_TO_GROUP_INDEX)
                    target = target.strip().lower()
                    context["step_id"] = _STEP_ID_MAP.get(target, target)
                return command, context

        return None

    def plan(self, message: str) -> Plan:
        """Delegate to the base planner for non-tour messages."""
        return self._base.plan(message)


__all__ = ["TourPlanner"]
