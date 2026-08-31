"""Collaboration exception hierarchy."""

from __future__ import annotations

from typing import Any

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class CollaborationError(EAIPError):
    """Base exception for all collaboration errors."""

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class SessionNotFoundError(CollaborationError):
    """Raised when a collaboration session is not found."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, session_id: str, **kwargs: Any) -> None:
        super().__init__(f"Collaboration session not found: {session_id}", **kwargs)


class TaskAssignmentError(CollaborationError):
    """Raised when a task cannot be assigned to an agent."""

    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION

    def __init__(self, task_id: str, reason: str = "", **kwargs: Any) -> None:
        msg = f"Task assignment failed: {task_id}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg, **kwargs)


class DelegationError(CollaborationError):
    """Raised when a delegation operation fails."""

    default_code: ErrorCode = ErrorCode.PROVIDER_UNAVAILABLE

    def __init__(self, delegation_id: str, reason: str = "", **kwargs: Any) -> None:
        msg = f"Delegation failed: {delegation_id}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg, **kwargs)


class ApprovalError(CollaborationError):
    """Raised when an approval operation fails."""

    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION

    def __init__(self, approval_id: str, reason: str = "", **kwargs: Any) -> None:
        msg = f"Approval failed: {approval_id}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg, **kwargs)


class ConsensusNotReachedError(CollaborationError):
    """Raised when consensus could not be reached within a session."""

    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION
    default_severity: ErrorSeverity = ErrorSeverity.WARNING

    def __init__(self, session_id: str, threshold: float = 0.0, **kwargs: Any) -> None:
        msg = f"Consensus not reached for session {session_id} (threshold={threshold})"
        super().__init__(msg, **kwargs)


__all__ = [
    "ApprovalError",
    "CollaborationError",
    "ConsensusNotReachedError",
    "DelegationError",
    "SessionNotFoundError",
    "TaskAssignmentError",
]
