"""Tests for aivalidator domain events."""

from __future__ import annotations

import pytest

from eaip.aivalidator.events import (
    RuleViolated,
    ValidationCompleted,
    ValidationFailed,
    ValidationStarted,
)
from eaip.aivalidator.models import RuleCategory
from eaip.events.event import DomainEvent


class TestValidationStarted:
    def test_defaults(self) -> None:
        e = ValidationStarted(run_id="r1", model_id="m1")
        assert e.event_type == "eaip.aivalidator.validation.started"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = ValidationStarted(run_id="r1", model_id="m1", rules_count=5)
        assert e.rules_count == 5


class TestValidationCompleted:
    def test_defaults(self) -> None:
        e = ValidationCompleted(run_id="r1", model_id="m1")
        assert e.event_type == "eaip.aivalidator.validation.completed"
        assert e.overall_score == 0.0

    def test_with_values(self) -> None:
        e = ValidationCompleted(
            run_id="r1", model_id="m1", overall_score=0.95, passed_rules=4, total_rules=5
        )
        assert e.overall_score == 0.95
        assert e.passed_rules == 4


class TestValidationFailed:
    def test_defaults(self) -> None:
        e = ValidationFailed(run_id="r1", model_id="m1")
        assert e.event_type == "eaip.aivalidator.validation.failed"

    def test_with_reason(self) -> None:
        e = ValidationFailed(run_id="r1", model_id="m1", reason="Bias threshold exceeded")
        assert e.reason == "Bias threshold exceeded"


class TestRuleViolated:
    def test_defaults(self) -> None:
        e = RuleViolated(rule_id="rl1", rule_name="no-bias", category=RuleCategory.BIAS)
        assert e.event_type == "eaip.aivalidator.rule.violated"
        assert e.metric_value == 0.0

    def test_with_values(self) -> None:
        e = RuleViolated(
            rule_id="rl1",
            rule_name="no-bias",
            category=RuleCategory.BIAS,
            metric_value=0.8,
            threshold=0.5,
        )
        assert e.metric_value == 0.8

    def test_frozen(self) -> None:
        e = RuleViolated(rule_id="rl1", rule_name="no-bias", category=RuleCategory.FAIRNESS)
        with pytest.raises((ValueError, TypeError)):
            e.rule_id = "rl2"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [ValidationStarted, ValidationCompleted, ValidationFailed, RuleViolated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
