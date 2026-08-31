"""Session & context domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class SessionEvent(DomainEvent):
    """Base event for all session events."""

    event_type: ClassVar[str] = "eaip.session.event"


class SessionCreated(SessionEvent):
    """Published when a new session is created."""

    event_type: ClassVar[str] = "eaip.session.created"
    session_id: str
    session_type: str
    tenant_id: str | None = None
    user_id: str | None = None


class SessionUpdated(SessionEvent):
    """Published when a session's attributes are updated."""

    event_type: ClassVar[str] = "eaip.session.updated"
    session_id: str
    changes: dict[str, Any]


class SessionClosed(SessionEvent):
    """Published when a session is closed."""

    event_type: ClassVar[str] = "eaip.session.closed"
    session_id: str


class SessionSuspended(SessionEvent):
    """Published when a session is suspended."""

    event_type: ClassVar[str] = "eaip.session.suspended"
    session_id: str


class SessionResumed(SessionEvent):
    """Published when a suspended session is resumed."""

    event_type: ClassVar[str] = "eaip.session.resumed"
    session_id: str


class SessionExpired(SessionEvent):
    """Published when a session expires."""

    event_type: ClassVar[str] = "eaip.session.expired"
    session_id: str


class ContextAttributeSet(SessionEvent):
    """Published when a context attribute is set."""

    event_type: ClassVar[str] = "eaip.session.context.attribute_set"
    scope: str
    scope_id: str
    key: str
    value: Any


class ContextPropagated(SessionEvent):
    """Published after context is propagated to target sessions."""

    event_type: ClassVar[str] = "eaip.session.context.propagated"
    source_session_id: str
    target_ids: list[str]
    attribute_count: int


class SessionTransferred(SessionEvent):
    """Published when a session is transferred to another user."""

    event_type: ClassVar[str] = "eaip.session.transferred"
    session_id: str
    source_user_id: str | None = None
    target_user_id: str


__all__ = [
    "ContextAttributeSet",
    "ContextPropagated",
    "SessionClosed",
    "SessionCreated",
    "SessionEvent",
    "SessionExpired",
    "SessionResumed",
    "SessionSuspended",
    "SessionTransferred",
    "SessionUpdated",
]
