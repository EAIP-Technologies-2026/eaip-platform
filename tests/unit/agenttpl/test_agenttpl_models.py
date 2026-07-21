"""Tests for :mod:`eaip.agenttpl.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.agenttpl.models import AgentTemplate, TemplateCategory, TemplateConfig, TemplateParameter


class TestTemplateParameter:
    """Tests for :class:`eaip.agenttpl.models.TemplateParameter`."""

    def test_create_minimal(self) -> None:
        """Test creating a parameter with required fields."""
        p = TemplateParameter(name="model", type="str")
        assert p.required is False
        assert p.default_value is None

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        p = TemplateParameter(name="n", type="str")
        with pytest.raises(ValidationError):
            p.name = "changed"


class TestAgentTemplate:
    """Tests for :class:`eaip.agenttpl.models.AgentTemplate`."""

    def test_create_minimal(self) -> None:
        """Test creating a template with required fields."""
        t = AgentTemplate(id="t1", name="Chat Bot", category=TemplateCategory.CHAT)
        assert t.is_deprecated is False
        assert t.version == "1.0.0"

    def test_full(self) -> None:
        """Test creating a template with all fields."""
        params = (TemplateParameter(name="model", type="str", required=True),)
        t = AgentTemplate(
            id="t2",
            name="Analyst",
            description="Data analyst agent",
            category=TemplateCategory.ANALYST,
            parameters=params,
            is_deprecated=True,
        )
        assert t.is_deprecated is True
        assert len(t.parameters) == 1

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        t = AgentTemplate(id="t1", name="Test", category=TemplateCategory.CUSTOM)
        with pytest.raises(ValidationError):
            t.name = "Changed"


class TestTemplateConfig:
    """Tests for :class:`eaip.agenttpl.models.TemplateConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = TemplateConfig()
        assert c.max_templates == 100
        assert c.allow_custom_templates is True

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = TemplateConfig(max_templates=50, allow_custom_templates=False)
        assert c.max_templates == 50
        assert c.allow_custom_templates is False

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = TemplateConfig()
        with pytest.raises(ValidationError):
            c.max_templates = 200


class TestTemplateCategory:
    """Tests for :class:`eaip.agenttpl.models.TemplateCategory`."""

    def test_values(self) -> None:
        """Test the enum values."""
        assert TemplateCategory.CHAT.value == "chat"
        assert TemplateCategory.TASK.value == "task"
        assert TemplateCategory.WORKFLOW.value == "workflow"
        assert TemplateCategory.ANALYST.value == "analyst"
        assert TemplateCategory.CUSTOM.value == "custom"


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        AgentTemplate(id="t1", name="Test", category=TemplateCategory.CUSTOM, unknown="val")
