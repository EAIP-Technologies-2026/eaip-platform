"""Tests for :mod:`eaip.labeling.events`."""

from __future__ import annotations

import pytest

from eaip.labeling.events import LabelReviewed, LabelSubmitted, TaskCompleted, TaskCreated


class TestTaskCreated:
    """Tests for :class:`eaip.labeling.events.TaskCreated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TaskCreated(task_id="t1", name="Classify", label_count=3)
        assert e.event_type == "eaip.labeling.task.created"
        assert e.label_count == 3

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = TaskCreated(task_id="t1", name="n", label_count=0)
        with pytest.raises(ValueError):
            e.task_id = "t2"


class TestTaskCompleted:
    """Tests for :class:`eaip.labeling.events.TaskCompleted`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TaskCompleted(task_id="t1", total_labels=5)
        assert e.event_type == "eaip.labeling.task.completed"


class TestLabelSubmitted:
    """Tests for :class:`eaip.labeling.events.LabelSubmitted`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = LabelSubmitted(label_id="l1", task_id="t1", labeler_id="u1", value="positive")
        assert e.event_type == "eaip.labeling.label.submitted"


class TestLabelReviewed:
    """Tests for :class:`eaip.labeling.events.LabelReviewed`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = LabelReviewed(label_id="l1", task_id="t1", approved=True)
        assert e.event_type == "eaip.labeling.label.reviewed"
        assert e.approved is True


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        TaskCreated(task_id="t1", name="n", label_count=0).event_type,
        TaskCompleted(task_id="t1", total_labels=0).event_type,
        LabelSubmitted(label_id="l1", task_id="t1", labeler_id="u1", value="v").event_type,
        LabelReviewed(label_id="l1", task_id="t1", approved=True).event_type,
    ]
    assert len(types) == len(set(types))
