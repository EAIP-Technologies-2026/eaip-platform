"""Investigation-aware intent routing for the Conductor planner.

Extends the existing ConductorPlanner with investigation-related intents.
Investigation commands are intercepted; all other messages pass through
to the underlying planner unchanged.
"""

from __future__ import annotations

import re

from eaip.copilot.planner import Plan, PlannedToolCall

# Investigation intent patterns checked in the main planner.
_INVESTIGATION_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # Create investigation
    (
        re.compile(
            r"\b(investigate|investigation)\b.*\b(why|what|how|failing|broken|issue)\b",
            re.I,
        ),
        "create_investigation",
        "create",
    ),
    # List investigations
    (
        re.compile(
            r"\b(list|show|my)\b.*\b(investigations?)\b", re.I
        ),
        "list_investigations",
        "list",
    ),
    # Continue/resume investigation
    (
        re.compile(
            r"\b(continue|resume)\b.*\b(investigation|my investigation)\b",
            re.I,
        ),
        "resume_investigation",
        "resume",
    ),
    # Get investigation details
    (
        re.compile(
            r"\b(show|get|what (?:is|about))\b.*\b(investigation)\b",
            re.I,
        ),
        "get_investigation",
        "get",
    ),
    # Pause investigation
    (
        re.compile(
            r"\b(pause)\b.*\b(investigation)\b", re.I
        ),
        "pause_investigation",
        "pause",
    ),
    # Resolve investigation
    (
        re.compile(
            r"\b(resolve|complete|finish)\b.*\b(investigation)\b",
            re.I,
        ),
        "resolve_investigation",
        "resolve",
    ),
    # What did we find
    (
        re.compile(
            r"\b(what did we (find|discover)|evidence|what (?:do|have) we know)\b",
            re.I,
        ),
        "get_investigation",
        "evidence",
    ),
    # What remains unresolved
    (
        re.compile(
            r"\b(what.*(unresolved|unsure|unknown)|open questions)\b",
            re.I,
        ),
        "get_investigation",
        "unresolved",
    ),
]


def extract_investigation_plan(
    text: str, message: str
) -> Plan | None:
    """Try to extract an investigation-related plan from the message.

    Args:
        text: Lowercased message text.
        message: Original message with preserved case.

    Returns:
        A Plan if an investigation intent matched, None otherwise.
    """
    for pattern, _tool_name, intent in _INVESTIGATION_PATTERNS:
        match = pattern.search(text)
        if match:
            if intent == "create":
                title = _extract_title(message)
                objective = _extract_objective(message)
                return Plan(
                    reply=(
                        f"I'll create an investigation into: {title}"
                    ),
                    tool_call=PlannedToolCall(
                        "create_investigation",
                        {"title": title, "objective": objective},
                    ),
                )
            if intent == "list":
                return Plan(
                    reply="Retrieving your investigations...",
                    tool_call=PlannedToolCall(
                        "list_investigations", {}
                    ),
                )
            if intent in ("resume", "get", "evidence", "unresolved"):
                # These need an investigation ID; they'll be handled
                # by the investigation-aware converse flow.
                return Plan(
                    reply=(
                        "Let me find your most recent investigation."
                    ),
                    tool_call=PlannedToolCall(
                        "list_investigations",
                        {"status": "active", "limit": 1},
                    ),
                )
            if intent == "pause":
                return Plan(
                    reply=(
                        "To pause an investigation, please "
                        "provide its ID."
                    ),
                )
            if intent == "resolve":
                return Plan(
                    reply=(
                        "To resolve an investigation, please "
                        "provide its ID and findings."
                    ),
                )
    return None


def _extract_title(message: str) -> str:
    """Extract a title from an investigation creation request."""
    # Remove common prefixes.
    cleaned = re.sub(
        r"^(please|can you|could you)\s+",
        "",
        message,
        flags=re.I,
    )
    cleaned = re.sub(
        r"\b(investigate|start an investigation|look into)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = cleaned.strip(" .?!")
    return cleaned[:120] if cleaned else "New Investigation"


def _extract_objective(message: str) -> str:
    """Extract an objective from an investigation creation request."""
    return f"Determine the root cause and status of: {_extract_title(message)}"


__all__ = ["extract_investigation_plan"]
