"""PolicyEngine — core policy evaluation with RBAC and ABAC."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from eaip.logging.context import get_logger
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.models import (
    ConditionOp,
    Policy,
    PolicyCondition,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
)


class PolicyEngine:
    """Evaluates policies against an evaluation context.

    Evaluation order:
      1. Only enabled policies are considered.
      2. Rules are evaluated in descending priority order.
      3. A rule matches when subject (RBAC), action, resource,
         and all conditions (ABAC) are satisfied.
      4. The first matching DENY rule short-circuits and denies.
      5. If no DENY matches, the highest-priority ALLOW wins.
      6. If no rules match at all, the decision is DENY (implicit deny).
    """

    def __init__(self) -> None:
        """Initialize the PolicyEngine."""
        self._log = get_logger("eaip.policy.engine")

    def evaluate(
        self,
        context: PolicyEvaluationContext,
        policies: list[Policy],
    ) -> PolicyDecision:
        """Evaluate all policies against the given context.

        Args:
            context: The evaluation context (who, what, where, when).
            policies: The list of policies to evaluate.

        Returns:
            A PolicyDecision with the result.
        """
        snapshot = context.model_dump()

        deny_rules: list[PolicyRule] = []
        allow_rules: list[PolicyRule] = []
        matched_ids: list[str] = []

        enabled_policies = [p for p in policies if p.enabled]
        all_rules = sorted(
            [r for p in enabled_policies for r in p.rules],
            key=lambda r: r.priority,
            reverse=True,
        )

        for rule in all_rules:
            if self._rule_matches(rule, context):
                matched_ids.append(rule.id)
                if rule.effect is PolicyEffect.DENY:
                    deny_rules.append(rule)
                else:
                    allow_rules.append(rule)

        if deny_rules:
            top = deny_rules[0]
            self._log.info(
                "policy.denied",
                rule=top.name,
                subject=context.subject_id,
                action=context.action,
                resource=context.resource,
            )
            return PolicyDecision(
                effect=PolicyEffect.DENY,
                matched_rules=tuple(r.id for r in deny_rules),
                context_snapshot=snapshot,
                explanation=f"Denied by rule {top.name!r}",
            )

        if allow_rules:
            top = allow_rules[0]
            self._log.info(
                "policy.allowed",
                rule=top.name,
                subject=context.subject_id,
                action=context.action,
                resource=context.resource,
            )
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                matched_rules=tuple(r.id for r in allow_rules),
                context_snapshot=snapshot,
                explanation=f"Allowed by rule {top.name!r}",
            )

        self._log.info(
            "policy.implicit_deny",
            subject=context.subject_id,
            action=context.action,
            resource=context.resource,
        )
        return PolicyDecision(
            effect=PolicyEffect.DENY,
            context_snapshot=snapshot,
            explanation="No matching rules — implicit deny",
        )

    @staticmethod
    def _evaluate_condition_bool(actual: Any, op: ConditionOp, value: Any) -> bool | None:
        """Evaluate comparison operators. Returns None if not a comparison op."""
        non_numeric = {
            ConditionOp.EQ,
            ConditionOp.NEQ,
            ConditionOp.IN,
            ConditionOp.NOT_IN,
            ConditionOp.MATCHES,
        }
        if op in non_numeric:
            return None
        try:
            actual_num = _to_number(actual)
            value_num = _to_number(value)
        except (TypeError, ValueError):
            return False
        cmp_map = {
            ConditionOp.GT: actual_num > value_num,
            ConditionOp.GTE: actual_num >= value_num,
            ConditionOp.LT: actual_num < value_num,
            ConditionOp.LTE: actual_num <= value_num,
        }
        return cmp_map.get(op, False)

    def _rule_matches(
        self,
        rule: PolicyRule,
        context: PolicyEvaluationContext,
    ) -> bool:
        if not self._subject_matches(rule, context):
            return False
        if not self._action_matches(rule, context):
            return False
        if not self._resource_matches(rule, context):
            return False
        return self._conditions_satisfied(rule, context)

    @staticmethod
    def _subject_matches(rule: PolicyRule, context: PolicyEvaluationContext) -> bool:
        if not rule.subjects:
            return True
        if context.subject_id in rule.subjects:
            return True
        return bool(set(context.subject_roles) & set(rule.subjects))

    @staticmethod
    def _action_matches(rule: PolicyRule, context: PolicyEvaluationContext) -> bool:
        if not rule.actions:
            return True
        return _pattern_match(context.action, rule.actions)

    @staticmethod
    def _resource_matches(rule: PolicyRule, context: PolicyEvaluationContext) -> bool:
        if not rule.resources:
            return True
        return _pattern_match(context.resource, rule.resources)

    @staticmethod
    def _conditions_satisfied(rule: PolicyRule, context: PolicyEvaluationContext) -> bool:
        if not rule.conditions:
            return True
        resolved = dict(context.attributes)
        resolved["subject_id"] = context.subject_id
        resolved["action"] = context.action
        resolved["resource"] = context.resource

        return all(_evaluate_condition(cond, resolved) for cond in rule.conditions)


def _pattern_match(value: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if pattern == "*":
            return True
        if pattern.endswith("*") and not pattern.startswith("*"):
            prefix = pattern[:-1]
            if value.startswith(prefix):
                return True
        elif pattern.startswith("*") and not pattern.endswith("*"):
            suffix = pattern[1:]
            if value.endswith(suffix):
                return True
        elif pattern.startswith("*") and pattern.endswith("*"):
            mid = pattern[1:-1]
            if mid in value:
                return True
        elif value == pattern:
            return True
    return False


def _evaluate_condition(cond: PolicyCondition, resolved: dict[str, Any]) -> bool:
    actual = resolved.get(cond.attribute)
    if cond.operator is ConditionOp.EXISTS:
        return actual is not None
    if actual is None:
        return False

    op = cond.operator
    handler = _CONDITION_HANDLERS.get(op)
    if handler is not None:
        return handler(actual, cond.value)
    result = PolicyEngine._evaluate_condition_bool(actual, op, cond.value)
    return result if result is not None else False


def _eval_in(actual: Any, value: Any) -> bool:
    """Check if actual is in value (list/tuple membership or substring)."""
    if isinstance(value, (list, tuple)):
        return actual in value
    return str(actual) in str(value)


def _eval_not_in(actual: Any, value: Any) -> bool:
    """Check if actual is not in value."""
    if isinstance(value, (list, tuple)):
        return actual not in value
    return str(actual) not in str(value)


_CONDITION_HANDLERS: dict[ConditionOp, Callable[[Any, Any], bool]] = {
    ConditionOp.EQ: lambda a, v: a == v,
    ConditionOp.NEQ: lambda a, v: a != v,
    ConditionOp.IN: _eval_in,
    ConditionOp.NOT_IN: _eval_not_in,
    ConditionOp.MATCHES: lambda a, v: bool(re.match(v, str(a))) if isinstance(v, str) else False,
}


def _to_number(value: Any) -> int | float:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return float(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to number")


__all__ = ["PolicyEngine"]
