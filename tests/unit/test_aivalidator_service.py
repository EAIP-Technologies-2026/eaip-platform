"""Tests for AIValidator."""

from __future__ import annotations

import pytest

from eaip.aivalidator.exceptions import AIValidationError, RuleNotFoundError
from eaip.aivalidator.models import (
    RuleCategory,
    ValidationResult,
    ValidationRule,
    ValidationRunStatus,
    ValidatorConfig,
)
from eaip.aivalidator.validator import AIValidator


class TestAIValidator:
    @pytest.fixture
    def validator(self) -> AIValidator:
        return AIValidator()

    @pytest.fixture
    def sample_rule(self) -> ValidationRule:
        return ValidationRule(
            id="rl1",
            name="no-bias",
            category=RuleCategory.BIAS,
            metric="demographic_parity",
            threshold=0.1,
        )

    class TestAddRule:
        async def test_adds_rule(self, validator: AIValidator, sample_rule: ValidationRule) -> None:
            result = await validator.add_rule(sample_rule)
            assert result.id == "rl1"

        async def test_stores_rule(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            stored = await validator.get_rule("rl1")
            assert stored.name == "no-bias"

    class TestGetRule:
        async def test_returns_rule(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            result = await validator.get_rule("rl1")
            assert result.metric == "demographic_parity"

        async def test_raises_on_missing(self, validator: AIValidator) -> None:
            with pytest.raises(RuleNotFoundError):
                await validator.get_rule("nonexistent")

    class TestDeleteRule:
        async def test_deletes_rule(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            await validator.delete_rule("rl1")
            assert await validator.list_rules() == []

        async def test_raises_on_missing(self, validator: AIValidator) -> None:
            with pytest.raises(RuleNotFoundError):
                await validator.delete_rule("nonexistent")

    class TestListRules:
        async def test_filters_by_category(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            r2 = ValidationRule(
                id="rl2",
                name="safe-output",
                category=RuleCategory.SAFETY,
                metric="toxicity",
                threshold=0.5,
            )
            await validator.add_rule(r2)
            rules = await validator.list_rules(category=RuleCategory.BIAS)
            assert len(rules) == 1

    class TestRunValidation:
        async def test_runs_validation(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            run = await validator.run_validation("m1", "run1")
            assert run.status == ValidationRunStatus.COMPLETED
            assert run.model_id == "m1"

        async def test_fails_without_rules(self, validator: AIValidator) -> None:
            with pytest.raises(AIValidationError):
                await validator.run_validation("m1", "run1")

        async def test_returns_run_with_results(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            run = await validator.run_validation("m1", "run1")
            assert isinstance(run.results, tuple)
            assert len(run.results) == 1

    class TestGetRun:
        async def test_returns_run(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            await validator.run_validation("m1", "run1")
            run = await validator.get_run("run1")
            assert run.id == "run1"

    class TestGetStatistics:
        async def test_returns_stats(
            self, validator: AIValidator, sample_rule: ValidationRule
        ) -> None:
            await validator.add_rule(sample_rule)
            stats = await validator.get_statistics()
            assert stats["total_rules"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = AIValidator()
            assert svc.config.max_parallel_rules == 4

        def test_custom_config(self) -> None:
            cfg = ValidatorConfig(max_parallel_rules=8)
            svc = AIValidator(config=cfg)
            assert svc.config.max_parallel_rules == 8
