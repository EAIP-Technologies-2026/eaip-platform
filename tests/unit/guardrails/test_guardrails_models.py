"""Tests for :mod:`eaip.guardrails.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.guardrails.models import GuardrailConfig, GuardrailResult, GuardrailRule


class TestGuardrailRule:
    """Tests for :class:`eaip.guardrails.models.GuardrailRule`."""

    def test_create_minimal(self) -> None:
        """Test creating a rule with minimal fields."""
        r = GuardrailRule(id="r1", name="Test Rule", pattern=".*")
        assert r.id == "r1"
        assert r.enabled is True
        assert r.priority == 0

    def test_create_full(self) -> None:
        """Test creating a rule with all fields."""
        r = GuardrailRule(
            id="r2",
            name="Full Rule",
            pattern="^[a-z]+$",
            enabled=False,
            priority=10,
            metadata={"owner": "team-a"},
        )
        assert r.enabled is False
        assert r.priority == 10

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        r = GuardrailRule(id="r1", name="Test", pattern=".*")
        with pytest.raises(ValidationError):
            r.name = "Changed"

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            GuardrailRule(id="r1", name="Test", pattern=".*", extra="x")


class TestGuardrailResult:
    """Tests for :class:`eaip.guardrails.models.GuardrailResult`."""

    def test_create_minimal(self) -> None:
        """Test creating a result with required fields."""
        result = GuardrailResult(rule_id="r1", passed=True)
        assert result.rule_id == "r1"
        assert result.passed is True
        assert result.message == ""

    def test_create_full(self) -> None:
        """Test creating a result with all fields."""
        result = GuardrailResult(
            rule_id="r1",
            passed=False,
            message="Violation detected",
            details={"field": "input"},
        )
        assert result.passed is False
        assert result.details["field"] == "input"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        result = GuardrailResult(rule_id="r1", passed=True)
        with pytest.raises(ValidationError):
            result.passed = False


class TestGuardrailConfig:
    """Tests for :class:`eaip.guardrails.models.GuardrailConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = GuardrailConfig()
        assert c.enabled is True
        assert c.max_rules == 100
        assert c.strict_mode is False

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = GuardrailConfig(enabled=False, max_rules=50, strict_mode=True)
        assert c.enabled is False
        assert c.max_rules == 50
        assert c.strict_mode is True

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = GuardrailConfig()
        with pytest.raises(ValidationError):
            c.enabled = False


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        GuardrailRule(id="r1", name="Test", pattern=".*", unknown="val")
