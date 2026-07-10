"""Tests for session domain events."""

from __future__ import annotations

from eaip.session.events import (
    ContextAttributeSet,
    ContextPropagated,
    SessionClosed,
    SessionCreated,
    SessionEvent,
    SessionExpired,
    SessionResumed,
    SessionSuspended,
    SessionTransferred,
    SessionUpdated,
)


class TestSessionEvents:
    def test_session_event_base(self) -> None:
        assert SessionEvent.event_type == "eaip.session.event"

    def test_session_created(self) -> None:
        event = SessionCreated(
            session_id="s1",
            session_type="user",
            tenant_id="t1",
            user_id="u1",
        )
        assert event.event_type == "eaip.session.created"
        assert event.session_id == "s1"
        assert event.session_type == "user"
        assert event.tenant_id == "t1"
        assert event.user_id == "u1"

    def test_session_updated(self) -> None:
        event = SessionUpdated(
            session_id="s1",
            changes={"metadata": {"key": "val"}},
        )
        assert event.event_type == "eaip.session.updated"
        assert event.session_id == "s1"
        assert event.changes["metadata"]["key"] == "val"

    def test_session_closed(self) -> None:
        event = SessionClosed(session_id="s1")
        assert event.event_type == "eaip.session.closed"
        assert event.session_id == "s1"

    def test_session_suspended(self) -> None:
        event = SessionSuspended(session_id="s1")
        assert event.event_type == "eaip.session.suspended"
        assert event.session_id == "s1"

    def test_session_resumed(self) -> None:
        event = SessionResumed(session_id="s1")
        assert event.event_type == "eaip.session.resumed"
        assert event.session_id == "s1"

    def test_session_expired(self) -> None:
        event = SessionExpired(session_id="s1")
        assert event.event_type == "eaip.session.expired"
        assert event.session_id == "s1"

    def test_context_attribute_set(self) -> None:
        event = ContextAttributeSet(
            scope="user",
            scope_id="u1",
            key="role",
            value="admin",
        )
        assert event.event_type == "eaip.session.context.attribute_set"
        assert event.scope == "user"
        assert event.scope_id == "u1"
        assert event.key == "role"
        assert event.value == "admin"

    def test_context_propagated(self) -> None:
        event = ContextPropagated(
            source_session_id="s1",
            target_ids=["s2", "s3"],
            attribute_count=5,
        )
        assert event.event_type == "eaip.session.context.propagated"
        assert event.source_session_id == "s1"
        assert event.target_ids == ["s2", "s3"]
        assert event.attribute_count == 5

    def test_session_transferred(self) -> None:
        event = SessionTransferred(
            session_id="s1",
            source_user_id="u1",
            target_user_id="u2",
        )
        assert event.event_type == "eaip.session.transferred"
        assert event.session_id == "s1"
        assert event.source_user_id == "u1"
        assert event.target_user_id == "u2"

    def test_events_are_frozen(self) -> None:
        event = SessionCreated(session_id="s1", session_type="user")
        try:
            event.session_id = "s2"
            assert False
        except Exception:
            pass

    def test_occurred_at_is_set(self) -> None:
        event = SessionCreated(session_id="s1", session_type="user")
        assert event.occurred_at is not None
