"""Tests for :mod:`eaip.contentmod.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.contentmod.events import (
    ContentApproved,
    ContentFlagged,
    ContentRejected,
    ContentSubmitted,
)
from eaip.events.event import DomainEvent


class TestContentSubmitted:
    def test_event_type(self) -> None:
        event = ContentSubmitted(content_id="c1", source="web", content_type="text")
        assert event.event_type == "eaip.contentmod.content.submitted"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ContentSubmitted(content_id="c1", source="web", content_type="text")
        assert event.content_id == "c1"
        assert event.source == "web"
        assert event.content_type == "text"


class TestContentApproved:
    def test_event_type(self) -> None:
        event = ContentApproved(content_id="c1", moderated_by="moderator1")
        assert event.event_type == "eaip.contentmod.content.approved"

    def test_fields(self) -> None:
        event = ContentApproved(content_id="c1", moderated_by="moderator1")
        assert event.moderated_by == "moderator1"


class TestContentRejected:
    def test_event_type(self) -> None:
        event = ContentRejected(content_id="c1", reason="inappropriate", moderated_by="mod1")
        assert event.event_type == "eaip.contentmod.content.rejected"


class TestContentFlagged:
    def test_event_type(self) -> None:
        event = ContentFlagged(content_id="c1", rule_id="r1", reason="matched pattern")
        assert event.event_type == "eaip.contentmod.content.flagged"


class TestEventImmutability:
    def test_frozen(self) -> None:
        event = ContentSubmitted(content_id="c1", source="web", content_type="text")
        with pytest.raises(ValidationError):
            event.content_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        event = ContentSubmitted(content_id="c1", source="web", content_type="text")
        assert event.occurred_at is not None
