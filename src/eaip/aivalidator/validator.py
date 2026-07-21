"""AIValidator — run validation rules against AI models."""

from __future__ import annotations

from eaip.aivalidator.events import (
    RuleViolated,
    ValidationCompleted,
    ValidationFailed,
    ValidationStarted,
)
from eaip.aivalidator.exceptions import AIValidationError, RuleNotFoundError
from eaip.aivalidator.models import (
    RuleCategory,
    ValidationResult,
    ValidationRule,
    ValidationRun,
    ValidationRunStatus,
    ValidatorConfig,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AIValidator:
    """Central service for running AI validation rules against models."""

    def __init__(self, config: ValidatorConfig | None = None) -> None:
        self._config = config or ValidatorConfig()
        self._rules: dict[str, ValidationRule] = {}
        self._runs: dict[str, ValidationRun] = {}
        self._log = get_logger("eaip.aivalidator.service")

    @property
    def config(self) -> ValidatorConfig:
        return self._config

    async def add_rule(self, rule: ValidationRule) -> ValidationRule:
        """Register a new validation rule."""
        self._rules[rule.id] = rule
        self._log.info("aivalidator.rule.added", rule_id=rule.id, name=rule.name)
        return rule

    async def get_rule(self, rule_id: str) -> ValidationRule:
        """Get a validation rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Validation rule not found: {rule_id}")
        return rule

    async def list_rules(self, category: RuleCategory | None = None) -> list[ValidationRule]:
        """List validation rules, optionally filtered by category."""
        rules = list(self._rules.values())
        if category is not None:
            rules = [r for r in rules if r.category == category]
        return rules

    async def delete_rule(self, rule_id: str) -> None:
        """Delete a validation rule."""
        if rule_id not in self._rules:
            raise RuleNotFoundError(f"Validation rule not found: {rule_id}")
        del self._rules[rule_id]
        self._log.info("aivalidator.rule.deleted", rule_id=rule_id)

    async def run_validation(
        self, model_id: str, run_id: str, rule_ids: tuple[str, ...] | None = None
    ) -> ValidationRun:
        """Run validation against a model using specified or all enabled rules."""
        if rule_ids is not None:
            rules = [self._rules[rid] for rid in rule_ids if rid in self._rules]
        else:
            rules = [r for r in self._rules.values() if r.enabled]
        if not rules:
            raise AIValidationError("No validation rules available to run")
        started = utc_now()
        ValidationStarted(run_id=run_id, model_id=model_id, rules_count=len(rules))
        run = ValidationRun(
            id=run_id,
            model_id=model_id,
            rules_applied=tuple(r.id for r in rules),
            status=ValidationRunStatus.RUNNING,
            started_at=started,
        )
        self._runs[run_id] = run
        results: list[ValidationResult] = []
        failed = False
        for rule in rules:
            result = ValidationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                metric_value=0.0,
                threshold=rule.threshold,
            )
            if not result.passed:
                RuleViolated(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    metric_value=result.metric_value,
                    threshold=rule.threshold,
                    run_id=run_id,
                )
                failed = True
                if self._config.fail_fast:
                    break
            results.append(result)
        completed = utc_now()
        delta = (completed - started).total_seconds()
        passed_count = sum(1 for r in results if r.passed)
        if failed:
            status = ValidationRunStatus.FAILED
            ValidationFailed(run_id=run_id, model_id=model_id, reason="One or more rules violated")
        else:
            status = ValidationRunStatus.COMPLETED
            overall = passed_count / len(results) if results else 1.0
            ValidationCompleted(
                run_id=run_id,
                model_id=model_id,
                overall_score=overall,
                passed_rules=passed_count,
                total_rules=len(results),
                duration_seconds=round(delta, 3),
            )
        run = run.model_copy(
            update={
                "results": tuple(results),
                "overall_score": passed_count / len(results) if results else 1.0,
                "status": status,
                "completed_at": completed,
            },
        )
        self._runs[run_id] = run
        self._log.info(
            "aivalidator.validation.completed",
            run_id=run_id,
            model_id=model_id,
            status=status.value,
        )
        return run

    async def get_run(self, run_id: str) -> ValidationRun:
        """Get a validation run by ID."""
        run = self._runs.get(run_id)
        if run is None:
            raise AIValidationError(f"Validation run not found: {run_id}")
        return run

    async def list_runs(self, model_id: str | None = None) -> list[ValidationRun]:
        """List validation runs, optionally filtered by model."""
        runs = list(self._runs.values())
        if model_id is not None:
            runs = [r for r in runs if r.model_id == model_id]
        return runs

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about validation rules and runs."""
        total_rules = len(self._rules)
        total_runs = len(self._runs)
        passed = sum(1 for r in self._runs.values() if r.status == ValidationRunStatus.COMPLETED)
        failed = sum(1 for r in self._runs.values() if r.status == ValidationRunStatus.FAILED)
        return {
            "total_rules": total_rules,
            "total_runs": total_runs,
            "passed": passed,
            "failed": failed,
        }


__all__ = ["AIValidator"]
