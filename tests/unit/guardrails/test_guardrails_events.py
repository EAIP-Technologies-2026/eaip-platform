"""Tests for :mod:`eaip.guardrails.events`."""

from __future__ import annotations

import pytest

from eaip.guardrails.events import GuardrailTriggered, InputValidated, OutputChecked


class TestInputValidated:
    """Tests for :class:`eaip.guardrails.events.InputValidated`."""

    def test_minimal(self) -> None:
        """Test creating an event with required fields."""
        e = InputValidated(input_id="in1", rule_id="r1", passed=True)
        assert e.event_type == "eaip.guardrails.input.validated"
        assert e.violations == ()

    def test_with_violations(self) -> None:
        """Test creating an event with violations."""
        e = InputValidated(input_id="in1", rule_id="r1", passed=False, violations=("profanity",))
        assert len(e.violations) == 1

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = InputValidated(input_id="in1", rule_id="r1", passed=True)
        with pytest.raises(ValueError):
            e.passed = False


class TestOutputChecked:
    """Tests for :class:`eaip.guardrails.events.OutputChecked`."""

    def test_minimal(self) -> None:
        """Test creating an event with required fields."""
        e = OutputChecked(output_id="out1", rule_id="r1", passed=True)
        assert e.event_type == "eaip.guardrails.output.checked"
        assert e.issues == ()

    def test_with_issues(self) -> None:
        """Test creating an event with issues."""
        e = OutputChecked(output_id="out1", rule_id="r1", passed=False, issues=("hallucination",))
        assert len(e.issues) == 1


class TestGuardrailTriggered:
    """Tests for :class:`eaip.guardrails.events.GuardrailTriggered`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = GuardrailTriggered(rule_id="r1", input_id="in1", action="block")
        assert e.event_type == "eaip.guardrails.rule.triggered"
        assert e.action == "block"

    def test_with_details(self) -> None:
        """Test creating an event with details."""
        e = GuardrailTriggered(
            rule_id="r1",
            input_id="in1",
            action="log",
            details={"severity": "high"},
        )
        assert e.details["severity"] == "high"


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        InputValidated(input_id="i", rule_id="r", passed=True).event_type,
        OutputChecked(output_id="o", rule_id="r", passed=True).event_type,
        GuardrailTriggered(rule_id="r", input_id="i", action="a").event_type,
    ]
    assert len(types) == len(set(types))
