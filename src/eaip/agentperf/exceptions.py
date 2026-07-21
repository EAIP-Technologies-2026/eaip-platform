"""Exception hierarchy for the agent performance analyzer."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AnalyzerError(EAIPError):
    """Base exception for agent performance analyzer errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class AgentNotFoundError(AnalyzerError):
    """Raised when an agent is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "AgentNotFoundError",
    "AnalyzerError",
]
