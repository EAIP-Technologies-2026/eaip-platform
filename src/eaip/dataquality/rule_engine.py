"""QualityRuleEngine — create, manage, and execute validation rules."""

from __future__ import annotations

import re
import time
from typing import Any, Literal, cast

from eaip.dataquality.exceptions import (
    QualityCheckNotFoundError,
    QualityRuleNotFoundError,
)
from eaip.dataquality.models import (
    DataQualityConfig,
    QualityCheck,
    QualityResult,
    QualityRule,
    QualityViolation,
)
from eaip.shared.time import utc_now


class QualityRuleEngine:
    """Manages rules and executes quality checks against data."""

    def __init__(self, config: DataQualityConfig | None = None) -> None:
        """Initialize the rule engine."""
        self._config = config or DataQualityConfig()
        self._rules: dict[str, QualityRule] = {}
        self._checks: dict[str, QualityCheck] = {}
        self._violations: list[QualityViolation] = []
        self._violation_counter: int = 0

    @property
    def config(self) -> DataQualityConfig:
        """Return the configuration."""
        return self._config

    def create_rule(self, rule: QualityRule) -> QualityRule:
        """Create a new quality rule."""
        self._rules[rule.id] = rule
        return rule

    def get(self, rule_id: str) -> QualityRule | None:
        """Get a rule by id, or None."""
        return self._rules.get(rule_id)

    def get_rule(self, rule_id: str) -> QualityRule:
        """Get a rule by id, raising if not found."""
        rule = self.get(rule_id)
        if rule is None:
            raise QualityRuleNotFoundError(
                f"Rule {rule_id!r} not found.",
                context={"rule_id": rule_id},
            )
        return rule

    def update_rule(self, rule_id: str, **kwargs: Any) -> QualityRule:
        """Update fields on a rule."""
        existing = self.get_rule(rule_id)
        updated = existing.model_copy(update=kwargs)
        self._rules[rule_id] = updated
        return updated

    def delete_rule(self, rule_id: str) -> QualityRule:
        """Delete a rule."""
        rule = self._rules.pop(rule_id, None)
        if rule is None:
            raise QualityRuleNotFoundError(
                f"Rule {rule_id!r} not found.",
                context={"rule_id": rule_id},
            )
        return rule

    def list_rules(self) -> list[QualityRule]:
        """Return all rules."""
        return list(self._rules.values())

    def create_check(self, check: QualityCheck) -> QualityCheck:
        """Create a new quality check."""
        self._checks[check.id] = check
        return check

    def get_check(self, check_id: str) -> QualityCheck:
        """Get a check by id, raising if not found."""
        check = self._checks.get(check_id)
        if check is None:
            raise QualityCheckNotFoundError(
                f"Check {check_id!r} not found.",
                context={"check_id": check_id},
            )
        return check

    def list_checks(self) -> list[QualityCheck]:
        """Return all checks."""
        return list(self._checks.values())

    async def validate(  # noqa: PLR0912
        self,
        rule: QualityRule,
        data: dict[str, Any],
    ) -> tuple[bool, list[QualityViolation]]:
        """Validate a single data record against a rule."""
        if not rule.enabled:
            return True, []

        violations: list[QualityViolation] = []
        field_value = data.get(rule.field)

        if rule.rule_type == "required":
            if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
                violations.append(self._make_violation(rule, data, field_value, "present"))

        elif rule.rule_type == "unique":
            if field_value is not None:
                pass

        elif rule.rule_type == "range":
            min_val = rule.params.get("min")
            max_val = rule.params.get("max")
            if isinstance(field_value, (int, float)):
                if min_val is not None and field_value < min_val:
                    violations.append(
                        self._make_violation(rule, data, field_value, f">= {min_val}")
                    )
                if max_val is not None and field_value > max_val:
                    violations.append(
                        self._make_violation(rule, data, field_value, f"<= {max_val}")
                    )

        elif rule.rule_type == "pattern":
            pattern = rule.params.get("pattern", "")
            if isinstance(field_value, str) and not re.match(pattern, field_value):
                violations.append(
                    self._make_violation(rule, data, field_value, f"pattern {pattern!r}")
                )

        elif rule.rule_type == "type":
            expected_type = rule.params.get("type", "str")
            if not self._check_type(field_value, expected_type):
                violations.append(self._make_violation(rule, data, field_value, expected_type))

        elif rule.rule_type == "custom":
            pass

        passed = len(violations) == 0
        self._violations.extend(violations)
        return passed, violations

    async def validate_all(
        self,
        rules: list[QualityRule],
        data: dict[str, Any],
    ) -> list[tuple[bool, list[QualityViolation]]]:
        """Validate data against multiple rules."""
        results = []
        for rule in rules:
            result = await self.validate(rule, data)
            results.append(result)
        return results

    async def execute_check(self, check_id: str) -> QualityResult:
        """Execute a quality check by id."""
        check = self.get_check(check_id)
        result_id = f"result-{check_id}-{id(check)}"
        started_at = utc_now()
        t0 = time.monotonic()

        rules_to_run = [self.get_rule(rid) for rid in check.rules]
        active_rules = [r for r in rules_to_run if r.enabled]
        total = len(active_rules)
        passed = 0
        failed = 0
        errors: list[str] = []

        for rule in active_rules:
            try:
                rule_passed, _ = await self.validate(rule, {})
                if rule_passed:
                    passed += 1
                else:
                    failed += 1
            except Exception as exc:
                errors.append(str(exc))
                failed += 1

        duration_ms = (time.monotonic() - t0) * 1000
        status: str = "passed" if failed == 0 else "failed"
        if errors:
            status = "error"

        return QualityResult(
            id=result_id,
            check_id=check_id,
            status=cast("Literal['passed', 'failed', 'error']", status),
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            errors=tuple(errors),
            started_at=started_at,
            completed_at=utc_now(),
            duration_ms=round(duration_ms, 2),
        )

    async def execute_all_checks(self) -> list[QualityResult]:
        """Execute all active quality checks."""
        results = []
        for check in self._checks.values():
            if check.status == "active":
                result = await self.execute_check(check.id)
                results.append(result)
        return results

    async def get_violations(
        self,
        rule_id: str,
        limit: int = 100,
    ) -> list[QualityViolation]:
        """Return violations for a specific rule."""
        filtered = [v for v in self._violations if v.rule_id == rule_id]
        return filtered[:limit]

    def _make_violation(
        self,
        rule: QualityRule,
        data: dict[str, Any],
        value: Any,
        expected: Any,
    ) -> QualityViolation:
        self._violation_counter += 1
        return QualityViolation(
            id=f"violation-{self._violation_counter}",
            rule_id=rule.id,
            record_id=data.get("id", ""),
            field=rule.field,
            value=value,
            expected=expected,
            severity=rule.severity,
            message=(
                f"Field {rule.field!r} {rule.rule_type} check failed:"
                f" expected {expected}, got {value!r}."
            ),
        )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "number": (int, float),
        }
        py_type = type_map.get(expected_type)
        if py_type is None:
            return True
        return isinstance(value, cast("type | tuple[type, ...]", py_type))


__all__ = ["QualityRuleEngine"]
