from __future__ import annotations

from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.models import (
    ConditionOp,
    Policy,
    PolicyCondition,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
)


def _policy(
    pid: str = "pol-1",
    rules: tuple[PolicyRule, ...] = (),
    enabled: bool = True,
) -> Policy:
    return Policy(id=pid, name=pid, rules=rules, enabled=enabled)


def _rule(
    rid: str = "r1",
    effect: PolicyEffect = PolicyEffect.ALLOW,
    subjects: tuple[str, ...] = (),
    actions: tuple[str, ...] = (),
    resources: tuple[str, ...] = (),
    conditions: tuple[PolicyCondition, ...] = (),
    priority: int = 0,
) -> PolicyRule:
    return PolicyRule(
        id=rid,
        name=rid,
        effect=effect,
        subjects=subjects,
        actions=actions,
        resources=resources,
        conditions=conditions,
        priority=priority,
    )


def _ctx(
    sid: str = "user-1",
    roles: tuple[str, ...] = (),
    action: str = "read",
    resource: str = "file",
    attrs: dict | None = None,
) -> PolicyEvaluationContext:
    return PolicyEvaluationContext(
        subject_id=sid,
        subject_roles=roles,
        action=action,
        resource=resource,
        attributes=attrs or {},
    )


class TestPolicyEngine:
    def test_empty_policies_implicit_deny(self) -> None:
        engine = PolicyEngine()
        ctx = _ctx()
        decision = engine.evaluate(ctx, [])
        assert decision.effect is PolicyEffect.DENY
        assert "implicit deny" in decision.explanation

    def test_no_matching_rule_implicit_deny(self) -> None:
        engine = PolicyEngine()
        rule = _rule(subjects=("admin",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(sid="user-1", roles=("viewer",))
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.DENY

    def test_disabled_policy_not_evaluated(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW)
        policies = [_policy(pid="pol-1", rules=(rule,), enabled=False)]
        ctx = _ctx()
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.DENY

    def test_rbac_allow_by_role(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, subjects=("admin",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(roles=("admin",))
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.ALLOW

    def test_rbac_deny_by_role(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.DENY, subjects=("banned",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(roles=("banned",))
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.DENY

    def test_rbac_allow_by_user_id(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, subjects=("user-42",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(sid="user-42")
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.ALLOW

    def test_deny_overrides_allow(self) -> None:
        engine = PolicyEngine()
        allow = _rule(rid="allow-r", effect=PolicyEffect.ALLOW)
        deny = _rule(rid="deny-r", effect=PolicyEffect.DENY, priority=1)
        policies = [_policy(rules=(allow, deny))]
        ctx = _ctx()
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.DENY
        assert "deny-r" in decision.matched_rules

    def test_action_matching_exact(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, actions=("read",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(action="read")
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_action_matching_wildcard(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, actions=("capability:*",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(action="capability:invoke")
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_action_not_matching(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, actions=("read",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(action="write")
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.DENY

    def test_resource_matching_wildcard(self) -> None:
        engine = PolicyEngine()
        rule = _rule(effect=PolicyEffect.ALLOW, resources=("capability:*",))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(resource="capability:agent.run")
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_eq(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="env", operator=ConditionOp.EQ, value="prod")
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"env": "prod"})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_not_satisfied(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="env", operator=ConditionOp.EQ, value="prod")
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"env": "dev"})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.DENY

    def test_abac_condition_exists(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="mfa", operator=ConditionOp.EXISTS)
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"mfa": True})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_gt(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="level", operator=ConditionOp.GT, value=3)
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"level": 5})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_gt_false(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="level", operator=ConditionOp.GT, value=3)
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"level": 2})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.DENY

    def test_abac_condition_in(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="region", operator=ConditionOp.IN, value=["us", "eu"])
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"region": "eu"})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_not_in(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="region", operator=ConditionOp.NOT_IN, value=["cn"])
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"region": "eu"})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_abac_condition_matches(self) -> None:
        engine = PolicyEngine()
        cond = PolicyCondition(attribute="email", operator=ConditionOp.MATCHES, value=r".+@example\.com")
        rule = _rule(effect=PolicyEffect.ALLOW, conditions=(cond,))
        policies = [_policy(rules=(rule,))]
        ctx = _ctx(attrs={"email": "user@example.com"})
        assert engine.evaluate(ctx, policies).effect is PolicyEffect.ALLOW

    def test_multiple_policies(self) -> None:
        engine = PolicyEngine()
        deny_rule = _rule(rid="dr1", effect=PolicyEffect.DENY, subjects=("bot",))
        allow_rule = _rule(rid="ar1", effect=PolicyEffect.ALLOW, subjects=("admin",))
        deny_pol = _policy(pid="deny-pol", rules=(deny_rule,))
        allow_pol = _policy(pid="allow-pol", rules=(allow_rule,))
        ctx = _ctx(roles=("admin",))
        decision = engine.evaluate(ctx, [deny_pol, allow_pol])
        assert decision.effect is PolicyEffect.ALLOW

    def test_priority_order(self) -> None:
        engine = PolicyEngine()
        low = _rule(rid="low", effect=PolicyEffect.ALLOW, priority=0)
        high = _rule(rid="high", effect=PolicyEffect.DENY, priority=100)
        policies = [_policy(rules=(low, high))]
        ctx = _ctx()
        decision = engine.evaluate(ctx, policies)
        assert decision.effect is PolicyEffect.DENY
        assert "high" in decision.matched_rules

    def test_decision_contains_context_snapshot(self) -> None:
        engine = PolicyEngine()
        ctx = _ctx(sid="user-x", roles=("admin",), action="deploy", resource="app", attrs={"env": "prod"})
        decision = engine.evaluate(ctx, [])
        snap = decision.context_snapshot
        assert snap["subject_id"] == "user-x"
        assert snap["action"] == "deploy"
        assert snap["resource"] == "app"
