"""Tests for :mod:`eaip.ciservice.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.ciservice.events import (
    BuildCompleted,
    BuildFailed,
    BuildStarted,
    PipelineCreated,
)
from eaip.ciservice.models import BuildStatus
from eaip.events.event import DomainEvent


class TestPipelineCreated:
    def test_event_type(self) -> None:
        event = PipelineCreated(
            pipeline_id="p1", name="CI Pipeline", repo_url="https://github.com/org/repo"
        )
        assert event.event_type == "eaip.ciservice.pipeline.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PipelineCreated(
            pipeline_id="p1", name="CI Pipeline", repo_url="https://github.com/org/repo"
        )
        assert event.pipeline_id == "p1"
        assert event.name == "CI Pipeline"
        assert event.repo_url == "https://github.com/org/repo"


class TestBuildStarted:
    def test_event_type(self) -> None:
        event = BuildStarted(build_id="b1", pipeline_id="p1", commit_sha="abc123")
        assert event.event_type == "eaip.ciservice.build.started"

    def test_fields(self) -> None:
        event = BuildStarted(build_id="b1", pipeline_id="p1", commit_sha="abc123")
        assert event.commit_sha == "abc123"


class TestBuildCompleted:
    def test_event_type(self) -> None:
        event = BuildCompleted(build_id="b1", pipeline_id="p1", status=BuildStatus.SUCCEEDED)
        assert event.event_type == "eaip.ciservice.build.completed"


class TestBuildFailed:
    def test_event_type(self) -> None:
        event = BuildFailed(build_id="b1", pipeline_id="p1", reason="test failure")
        assert event.event_type == "eaip.ciservice.build.failed"


class TestEventImmutability:
    def test_frozen(self) -> None:
        event = PipelineCreated(pipeline_id="p1", name="CI", repo_url="https://github.com/org/repo")
        with pytest.raises(ValidationError):
            event.pipeline_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        event = PipelineCreated(pipeline_id="p1", name="CI", repo_url="https://github.com/org/repo")
        assert event.occurred_at is not None
