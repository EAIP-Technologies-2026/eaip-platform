"""Tests for :mod:`eaip.modelreg.events`."""

from __future__ import annotations

import pytest

from eaip.modelreg.events import ModelArchived, ModelDeprecated, ModelRegistered, ModelVersioned


class TestModelRegistered:
    """Tests for :class:`eaip.modelreg.events.ModelRegistered`."""

    def test_minimal(self) -> None:
        """Test creating an event with required fields."""
        e = ModelRegistered(model_id="m1", name="GPT-4", provider="openai")
        assert e.event_type == "eaip.modelreg.model.registered"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = ModelRegistered(model_id="m1", name="n", provider="p")
        with pytest.raises(ValueError):
            e.model_id = "m2"


class TestModelVersioned:
    """Tests for :class:`eaip.modelreg.events.ModelVersioned`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = ModelVersioned(model_id="m1", version="1.0.0")
        assert e.event_type == "eaip.modelreg.model.versioned"
        assert e.artifacts == ()

    def test_with_artifacts(self) -> None:
        """Test creating an event with artifacts."""
        e = ModelVersioned(model_id="m1", version="1.0.0", artifacts=("a1",))
        assert len(e.artifacts) == 1


class TestModelDeprecated:
    """Tests for :class:`eaip.modelreg.events.ModelDeprecated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = ModelDeprecated(model_id="m1", reason="superseded")
        assert e.event_type == "eaip.modelreg.model.deprecated"
        assert e.reason == "superseded"


class TestModelArchived:
    """Tests for :class:`eaip.modelreg.events.ModelArchived`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = ModelArchived(model_id="m1")
        assert e.event_type == "eaip.modelreg.model.archived"


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        ModelRegistered(model_id="m1", name="n", provider="p").event_type,
        ModelVersioned(model_id="m1", version="v").event_type,
        ModelDeprecated(model_id="m1").event_type,
        ModelArchived(model_id="m1").event_type,
    ]
    assert len(types) == len(set(types))
