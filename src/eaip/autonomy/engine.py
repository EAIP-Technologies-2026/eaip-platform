from __future__ import annotations

from typing import Any

from eaip.autonomy.models import AutonomyDecision, AutonomyLevel, AutonomyPolicy

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class AutonomyEngine:
    def __init__(self) -> None:
        self._policies: dict[str, AutonomyPolicy] = {}

    def put_policy(self, policy: AutonomyPolicy) -> AutonomyPolicy:
        self._policies[f"{policy.tenant_id}:{policy.policy_id}"] = policy
        return policy

    def get_policy(self, policy_id: str, tenant_id: str) -> AutonomyPolicy | None:
        return self._policies.get(f"{tenant_id}:{policy_id}")

    def list_for_tenant(self, tenant_id: str) -> list[AutonomyPolicy]:
        return [v for k, v in self._policies.items() if k.startswith(f"{tenant_id}:")]

    def evaluate(self, tenant_id: str, action: str, tool: str = "", connector: str = "", risk: str = "low", budget: float = 0, level: str = "L2") -> dict[str, Any]:
        policies = self.list_for_tenant(tenant_id)
        if not policies:
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": "no policy — default require approval"}
        pol = policies[0]
        level_order = {e.value: i for i, e in enumerate(AutonomyLevel)}
        req = level_order.get(level, 1)
        max_allowed = level_order.get(pol.max_level.value, 1)
        if req > max_allowed:
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": f"level {level} exceeds max {pol.max_level.value}"}
        if tool and tool in pol.blocked_tools:
            return {"decision": AutonomyDecision.DENY.value, "reason": f"tool {tool!r} blocked"}
        if pol.allowed_tools and tool and tool not in pol.allowed_tools:
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": f"tool {tool!r} not in allowlist"}
        if action in pol.require_approval_for:
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": f"action {action!r} requires approval"}
        if budget and pol.max_budget and budget > pol.max_budget:
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": "budget exceeds policy"}
        if RISK_ORDER.get(risk, 0) >= 2 and level not in ("L0", "L1"):
            return {"decision": AutonomyDecision.REQUIRE_APPROVAL.value, "reason": f"risk {risk} requires approval"}
        if connector and pol.allowed_connectors and connector not in pol.allowed_connectors:
            return {"decision": AutonomyDecision.DENY.value, "reason": f"connector {connector!r} not allowed"}
        return {"decision": AutonomyDecision.ALLOW.value, "reason": "allowed by policy", "policy_id": pol.policy_id}


__all__ = ["AutonomyEngine"]
