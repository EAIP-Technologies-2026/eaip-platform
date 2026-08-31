"""Tests for :mod:`eaip.labeling.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.labeling.models import Label, LabelerAssignment, LabelingConfig, LabelingTask


class TestLabelingTask:
    """Tests for :class:`eaip.labeling.models.LabelingTask`."""

    def test_create_minimal(self) -> None:
        """Test creating a task with required fields."""
        t = LabelingTask(id="t1", name="Classify intent")
        assert t.status == "pending"
        assert t.labels == ()

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        t = LabelingTask(id="t1", name="Test")
        with pytest.raises(ValidationError):
            t.name = "Changed"


class TestLabel:
    """Tests for :class:`eaip.labeling.models.Label`."""

    def test_create_minimal(self) -> None:
        """Test creating a label with required fields."""
        label = Label(id="l1", task_id="t1", labeler_id="u1", value="positive")
        assert label.confidence == 1.0
        assert label.reviewed is False

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        label = Label(id="l1", task_id="t1", labeler_id="u1", value="v")
        with pytest.raises(ValidationError):
            label.value = "changed"


class TestLabelerAssignment:
    """Tests for :class:`eaip.labeling.models.LabelerAssignment`."""

    def test_create(self) -> None:
        """Test creating an assignment with required fields."""
        a = LabelerAssignment(task_id="t1", labeler_id="u1")
        assert a.completed is False

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        a = LabelerAssignment(task_id="t1", labeler_id="u1")
        with pytest.raises(ValidationError):
            a.completed = True


class TestLabelingConfig:
    """Tests for :class:`eaip.labeling.models.LabelingConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = LabelingConfig()
        assert c.min_labelers_per_task == 1
        assert c.max_labelers_per_task == 5
        assert c.require_review is True

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = LabelingConfig(
            min_labelers_per_task=2,
            max_labelers_per_task=3,
            require_review=False,
            auto_approve_threshold=0.95,
        )
        assert c.min_labelers_per_task == 2
        assert c.require_review is False
        assert c.auto_approve_threshold == 0.95

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = LabelingConfig()
        with pytest.raises(ValidationError):
            c.min_labelers_per_task = 3


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        LabelingTask(id="t1", name="Test", unknown="val")
