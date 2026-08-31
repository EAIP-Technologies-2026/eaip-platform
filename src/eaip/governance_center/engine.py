"""Enterprise Governance Engine (EGE) — deterministic, explainable governance decisions."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GovernanceDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"
    APPROVAL = "APPROVAL"
    ESCALATE = "ESCALATE"


class PolicyCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    operator: str = "equals"
    value: Any = None


class PolicyRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    conditions: tuple[PolicyCondition, ...] = Field(default_factory=tuple)
    effect: GovernanceDecision = GovernanceDecision.ALLOW
    priority: int = 0
    scope: str = "global"
    enabled: bool = True


class GovernanceDecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    who: str
    what: str
    why: str = ""
    data_ref: str = ""
    system_ref: str = ""
    action: str = ""
    risk_level: str = "low"
    cost_estimate: float = 0.0
    autonomy_level: str = "L2"
    decision: GovernanceDecision = GovernanceDecision.ALLOW
    reason: str = ""
    policy_ids: tuple[str, ...] = Field(default_factory=tuple)
    created_at: Any = Field(default_factory=utc_now)


class EnterpriseGovernanceEngine:
    """Deterministic, explainable governance engine combining autonomy and policy evaluation."""

    def __init__(self, autonomy_engine: Any = None, policy_engine: Any = None, event_bus: Any = None) -> None:
        self._autonomy = autonomy_engine
        self._policy_engine = policy_engine
        self._event_bus = event_bus
        self._policies: dict[str, PolicyRule] = {}
        self._decisions: dict[str, GovernanceDecisionRecord] = {}

    def _key(self, tenant_id: str, entity_id: str) -> str:
        return f"{tenant_id}:{entity_id}"

    def register_policy(self, policy: PolicyRule) -> PolicyRule:
        self._policies[self._key(policy.tenant_id, policy.id)] = policy
        return policy

    def list_policies(self, tenant_id: str) -> list[PolicyRule]:
        return [v for k, v in self._policies.items() if k.startswith(f"{tenant_id}:")]

    def get_decision_history(self, tenant_id: str) -> list[GovernanceDecisionRecord]:
        return sorted(
            [v for k, v in self._decisions.items() if k.startswith(f"{tenant_id}:")],
            key=lambda d: d.created_at,
            reverse=True,
        )

    def evaluate_action(
        self,
        tenant_id: str,
        who: str,
        what: str,
        why: str = "",
        data_ref: str = "",
        system_ref: str = "",
        action: str = "",
        risk_level: str = "low",
        cost_estimate: float = 0.0,
        autonomy_level: str = "L2",
        permission: str = "",
    ) -> GovernanceDecisionRecord:
        decision = GovernanceDecision.ALLOW
        reasons: list[str] = []
        matched_policy_ids: list[str] = []

        # autonomy check
        if self._autonomy:
            auto_result = self._autonomy.evaluate(
                tenant_id=tenant_id, action=action or what, level=autonomy_level,
                risk=risk_level, budget=cost_estimate,
            )
            auto_decision = auto_result.get("decision", "ALLOW")
            if auto_decision == "DENY":
                decision = GovernanceDecision.DENY
                reasons.append(f"autonomy: {auto_result.get('reason', 'denied')}")
            elif auto_decision == "REQUIRE_APPROVAL":
                decision = GovernanceDecision.APPROVAL
                reasons.append(f"autonomy: {auto_result.get('reason', 'requires approval')} requires approval")

        # policy evaluation
        policies = self.list_policies(tenant_id)
        for policy in sorted(policies, key=lambda p: p.priority, reverse=True):
            if not policy.enabled:
                continue
            if self._matches_policy(policy, who=who, what=what, action=action, risk=risk_level, autonomy=autonomy_level, cost=cost_estimate):
                matched_policy_ids.append(policy.id)
                if policy.effect == GovernanceDecision.DENY:
                    decision = GovernanceDecision.DENY
                    reasons.append(f"policy '{policy.name}' denies")
                elif policy.effect == GovernanceDecision.APPROVAL and decision != GovernanceDecision.DENY:
                    decision = GovernanceDecision.APPROVAL
                    reasons.append(f"policy '{policy.name}' requires approval")
                elif policy.effect == GovernanceDecision.ESCALATE and decision == GovernanceDecision.ALLOW:
                    decision = GovernanceDecision.ESCALATE
                    reasons.append(f"policy '{policy.name}' escalates")
                elif policy.effect == GovernanceDecision.MODIFY and decision == GovernanceDecision.ALLOW:
                    decision = GovernanceDecision.MODIFY
                    reasons.append(f"policy '{policy.name}' modifies")

        # external policy engine
        if self._policy_engine and decision == GovernanceDecision.ALLOW:
            try:
                ext_result = self._policy_engine.evaluate(tenant_id=tenant_id, action=action or what)
                if isinstance(ext_result, dict) and ext_result.get("decision") == "DENY":
                    decision = GovernanceDecision.DENY
                    reasons.append(f"external_policy: {ext_result.get('reason', 'denied')}")
            except Exception:
                pass

        if not reasons:
            reasons.append("all checks passed")

        record_id = f"gov-{uuid.uuid4().hex[:8]}"
        record = GovernanceDecisionRecord(
            id=record_id, tenant_id=tenant_id, who=who, what=what, why=why,
            data_ref=data_ref, system_ref=system_ref, action=action,
            risk_level=risk_level, cost_estimate=cost_estimate,
            autonomy_level=autonomy_level, decision=decision,
            reason="; ".join(reasons), policy_ids=tuple(matched_policy_ids),
        )
        self._decisions[self._key(tenant_id, record_id)] = record
        self._publish("governance.decision.made", {"decision_id": record_id, "tenant_id": tenant_id, "decision": decision.value, "who": who, "what": what})
        return record

    def check_policy(self, tenant_id: str, policy_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = self._policies.get(self._key(tenant_id, policy_id))
        if not policy:
            return {"found": False, "policy_id": policy_id}
        matches = self._matches_policy(
            policy,
            who=context.get("who", "") if context else "",
            what=context.get("what", "") if context else "",
            action=context.get("action", "") if context else "",
            risk=context.get("risk", "low") if context else "low",
            autonomy=context.get("autonomy", "L2") if context else "L2",
            cost=context.get("cost", 0) if context else 0,
        )
        return {"found": True, "policy_id": policy_id, "name": policy.name, "effect": policy.effect.value, "matches": matches, "enabled": policy.enabled}

    def _matches_policy(self, policy: PolicyRule, **kwargs: Any) -> bool:
        if not policy.conditions:
            return True
        for cond in policy.conditions:
            actual = kwargs.get(cond.field, "")
            if cond.operator == "equals" and actual != cond.value:
                return False
            elif cond.operator == "in" and actual not in (cond.value if isinstance(cond.value, (list, tuple)) else [cond.value]):
                return False
            elif cond.operator == "gt" and not (isinstance(actual, (int, float)) and actual > cond.value):
                return False
            elif cond.operator == "contains" and isinstance(actual, str) and cond.value not in actual:
                return False
        return True

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            import asyncio
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass


__all__ = [
    "EnterpriseGovernanceEngine",
    "GovernanceDecision",
    "GovernanceDecisionRecord",
    "PolicyCondition",
    "PolicyRule",
]
