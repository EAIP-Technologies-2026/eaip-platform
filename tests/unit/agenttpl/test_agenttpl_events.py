"""Tests for :mod:`eaip.agenttpl.events`."""

from __future__ import annotations

import pytest

from eaip.agenttpl.events import (
    TemplateApplied,
    TemplateCreated,
    TemplateDeprecated,
    TemplateUpdated,
)
from eaip.agenttpl.models import TemplateCategory


class TestTemplateCreated:
    """Tests for :class:`eaip.agenttpl.events.TemplateCreated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TemplateCreated(template_id="t1", name="Chat Bot", category=TemplateCategory.CHAT)
        assert e.event_type == "eaip.agenttpl.template.created"
        assert e.category is TemplateCategory.CHAT

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = TemplateCreated(template_id="t1", name="n", category=TemplateCategory.CUSTOM)
        with pytest.raises(ValueError):
            e.template_id = "t2"


class TestTemplateUpdated:
    """Tests for :class:`eaip.agenttpl.events.TemplateUpdated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TemplateUpdated(template_id="t1", changes={"name": "New Name"})
        assert e.event_type == "eaip.agenttpl.template.updated"
        assert e.changes["name"] == "New Name"


class TestTemplateDeprecated:
    """Tests for :class:`eaip.agenttpl.events.TemplateDeprecated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TemplateDeprecated(template_id="t1", reason="old version")
        assert e.event_type == "eaip.agenttpl.template.deprecated"


class TestTemplateApplied:
    """Tests for :class:`eaip.agenttpl.events.TemplateApplied`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = TemplateApplied(
            template_id="t1",
            agent_id="a1",
            parameters={"model": "gpt-4"},
        )
        assert e.event_type == "eaip.agenttpl.template.applied"
        assert e.agent_id == "a1"


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        TemplateCreated(template_id="t1", name="n", category=TemplateCategory.CUSTOM).event_type,
        TemplateUpdated(template_id="t1").event_type,
        TemplateDeprecated(template_id="t1").event_type,
        TemplateApplied(template_id="t1", agent_id="a1").event_type,
    ]
    assert len(types) == len(set(types))
