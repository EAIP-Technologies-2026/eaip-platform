"""Connector policy engine — gate every invocation through policy checks."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class PolicyDecision(StrEnum):
    """Policy decision outcomes."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    APPROVAL = "APPROVAL"


class ConnectorPolicyRule(BaseModel):
    """A policy rule for connector invocations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    tenant_id: str
    connector_id: str = ""
    connector_type: str = ""
    allowed_operations: list[str] = Field(default_factory=list)
    denied_operations: list[str] = Field(default_factory=list)
    allowed_roles: list[str] = Field(default_factory=list)
    max_data_classification: str = "internal"
    max_autonomy_level: str = "L2"
    requires_approval_above: str = "L2"
    max_cost_per_invocation: float = 0.0
    enabled: bool = True
    created_at: Any = Field(default_factory=utc_now)


class ConnectorInvocationContext(BaseModel):
    """Context for a connector invocation policy check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    connector_id: str
    operation: str
    data_classification: str = "internal"
    autonomy_level: str = "L2"
    user_roles: list[str] = Field(default_factory=list)
    estimated_cost: float = 0.0


class PolicyCheckResult(BaseModel):
    """Result of a connector policy check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: PolicyDecision
    reason: str
    rule_id: str = ""
    requires_approval: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


DATA_CLASSIFICATION_ORDER = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
AUTONOMY_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


class ConnectorPolicyEngine:
    """Policy engine for connector invocations.

    Every connector invocation must pass through check_invocation().
    Checks: tenant, permission, data policy, autonomy, risk, budget, connector policy.
    """

    def __init__(self) -> None:
        self._rules: dict[str, ConnectorPolicyRule] = {}
        self._log = get_logger("eaip.connectors.policy")

    def add_rule(self, rule: ConnectorPolicyRule) -> ConnectorPolicyRule:
        """Add a policy rule."""
        key = f"{rule.tenant_id}:{rule.rule_id}"
        self._rules[key] = rule
        self._log.info("policy.rule_added", rule_id=rule.rule_id, tenant_id=rule.tenant_id)
        return rule

    def get_rules(self, tenant_id: str) -> list[ConnectorPolicyRule]:
        """Get all policy rules for a tenant."""
        return [v for k, v in self._rules.items() if k.startswith(f"{tenant_id}:")]

    def check_invocation(self, context: ConnectorInvocationContext) -> PolicyCheckResult:
        """Check if a connector invocation is allowed.

        Returns ALLOW, DENY, or APPROVAL.
        """
        rules = self.get_rules(context.tenant_id)
        if not rules:
            return PolicyCheckResult(
                decision=PolicyDecision.APPROVAL,
                reason="No policy rules defined — defaulting to approval required",
            )

        for rule in rules:
            if not rule.enabled:
                continue
            if rule.connector_id and rule.connector_id != context.connector_id:
                continue
            result = self._evaluate_rule(rule, context)
            if result.decision == PolicyDecision.DENY:
                return result
            if result.decision == PolicyDecision.APPROVAL:
                return result

        return PolicyCheckResult(
            decision=PolicyDecision.ALLOW,
            reason="Allowed by connector policy",
        )

    def _evaluate_rule(
        self, rule: ConnectorPolicyRule, context: ConnectorInvocationContext
    ) -> PolicyCheckResult:
        """Evaluate a single policy rule against invocation context."""
        if rule.denied_operations and context.operation in rule.denied_operations:
            return PolicyCheckResult(
                decision=PolicyDecision.DENY,
                reason=f"Operation '{context.operation}' is explicitly denied",
                rule_id=rule.rule_id,
            )

        if rule.allowed_operations and context.operation not in rule.allowed_operations:
            return PolicyCheckResult(
                decision=PolicyDecision.DENY,
                reason=f"Operation '{context.operation}' not in allowed operations",
                rule_id=rule.rule_id,
            )

        if rule.allowed_roles and context.user_roles:
            if not any(r in rule.allowed_roles for r in context.user_roles):
                return PolicyCheckResult(
                    decision=PolicyDecision.DENY,
                    reason="User role not permitted for this connector",
                    rule_id=rule.rule_id,
                )

        ctx_class_level = DATA_CLASSIFICATION_ORDER.get(context.data_classification, 1)
        rule_class_level = DATA_CLASSIFICATION_ORDER.get(rule.max_data_classification, 1)
        if ctx_class_level > rule_class_level:
            return PolicyCheckResult(
                decision=PolicyDecision.DENY,
                reason=f"Data classification '{context.data_classification}' exceeds max '{rule.max_data_classification}'",
                rule_id=rule.rule_id,
            )

        ctx_autonomy = AUTONOMY_ORDER.get(context.autonomy_level, 2)
        rule_max_autonomy = AUTONOMY_ORDER.get(rule.max_autonomy_level, 2)
        rule_approval = AUTONOMY_ORDER.get(rule.requires_approval_above, 2)
        if ctx_autonomy > rule_max_autonomy:
            return PolicyCheckResult(
                decision=PolicyDecision.DENY,
                reason=f"Autonomy level '{context.autonomy_level}' exceeds max '{rule.max_autonomy_level}'",
                rule_id=rule.rule_id,
            )
        if ctx_autonomy > rule_approval:
            return PolicyCheckResult(
                decision=PolicyDecision.APPROVAL,
                reason=f"Autonomy level '{context.autonomy_level}' requires approval above '{rule.requires_approval_above}'",
                rule_id=rule.rule_id,
                requires_approval=True,
            )

        if rule.max_cost_per_invocation > 0 and context.estimated_cost > rule.max_cost_per_invocation:
            return PolicyCheckResult(
                decision=PolicyDecision.APPROVAL,
                reason=f"Estimated cost {context.estimated_cost} exceeds max {rule.max_cost_per_invocation}",
                rule_id=rule.rule_id,
                requires_approval=True,
            )

        return PolicyCheckResult(
            decision=PolicyDecision.ALLOW,
            reason="Allowed by rule",
            rule_id=rule.rule_id,
        )

    def remove_rule(self, rule_id: str, tenant_id: str) -> bool:
        """Remove a policy rule."""
        return self._rules.pop(f"{tenant_id}:{rule_id}", None) is not None


__all__ = [
    "ConnectorInvocationContext",
    "ConnectorPolicyEngine",
    "ConnectorPolicyRule",
    "PolicyCheckResult",
    "PolicyDecision",
]
