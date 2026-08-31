"""Tests for :mod:`eaip.curation.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.curation.events import (
    ContentApproved,
    ContentFlagged,
    ContentRejected,
    ContentSubmitted,
)

ContentSubmitted.__test__ = False
ContentApproved.__test__ = False
ContentRejected.__test__ = False
ContentFlagged.__test__ = False


class TestCurationEvents:
    def test_content_submitted(self) -> None:
        e = ContentSubmitted(
            submission_id="sub1",
            source="wiki",
            content_type="text",
            submitted_by="user1",
        )
        assert e.event_type == "eaip.curation.content.submitted"
        assert e.submission_id == "sub1"
        assert e.source == "wiki"

    def test_content_approved(self) -> None:
        e = ContentApproved(submission_id="sub1", reviewer="reviewer1", score=0.95)
        assert e.event_type == "eaip.curation.content.approved"
        assert e.reviewer == "reviewer1"
        assert e.score == 0.95

    def test_content_approved_none_score(self) -> None:
        e = ContentApproved(submission_id="sub1", reviewer="reviewer1", score=None)
        assert e.score is None

    def test_content_rejected(self) -> None:
        e = ContentRejected(submission_id="sub1", reviewer="reviewer1", reason="not relevant")
        assert e.event_type == "eaip.curation.content.rejected"
        assert e.reason == "not relevant"

    def test_content_flagged(self) -> None:
        e = ContentFlagged(submission_id="sub1", flagged_by="moderator", reason="inappropriate")
        assert e.event_type == "eaip.curation.content.flagged"
        assert e.flagged_by == "moderator"


class TestEventImmutability:
    def test_submitted_frozen(self) -> None:
        e = ContentSubmitted(
            submission_id="s1", source="wiki", content_type="text", submitted_by="u1"
        )
        with pytest.raises(ValidationError):
            e.submission_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        e = ContentSubmitted(
            submission_id="s1", source="wiki", content_type="text", submitted_by="u1"
        )
        assert e.occurred_at is not None
