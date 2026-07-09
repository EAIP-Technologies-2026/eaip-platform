from __future__ import annotations

from eaip.policy.models import (
    ConditionOp,
    Policy,
    PolicyCondition,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
)


class TestPolicyEffect:
    def test_enum_values(self) -> None:
        assert PolicyEffect.ALLOW.value == "allow"
        assert PolicyEffect.DENY.value == "deny"


class TestConditionOp:
    def test_all_operators_defined(self) -> None:
        assert ConditionOp.EQ.value == "eq"
        assert ConditionOp.MATCHES.value == "matches"


class TestPolicyCondition:
    def test_create_eq_condition(self) -> None:
        c = PolicyCondition(attribute="user.department", operator=ConditionOp.EQ, value="engineering")
        assert c.attribute == "user.department"
        assert c.operator is ConditionOp.EQ
        assert c.value == "engineering"

    def test_create_exists_condition(self) -> None:
        c = PolicyCondition(attribute="user.mfa_enabled", operator=ConditionOp.EXISTS)
        assert c.operator is ConditionOp.EXISTS
        assert c.value is None

    def test_condition_is_frozen(self) -> None:
        c = PolicyCondition(attribute="a", operator=ConditionOp.EQ, value=1)
        import pydantic
        try:
            c.attribute = "b"
            assert False, "should be frozen"
        except pydantic.ValidationError:
            pass


class TestPolicyRule:
    def test_minimal_rule(self) -> None:
        r = PolicyRule(id="rule-1", name="test-rule", effect=PolicyEffect.ALLOW)
        assert r.id == "rule-1"
        assert r.effect is PolicyEffect.ALLOW
        assert r.subjects == ()
        assert r.actions == ()
        assert r.resources == ()
        assert r.conditions == ()
        assert r.priority == 0

    def test_full_rule(self) -> None:
        cond = PolicyCondition(attribute="env", operator=ConditionOp.EQ, value="prod")
        r = PolicyRule(
            id="rule-2",
            name="Full Rule",
            effect=PolicyEffect.DENY,
            subjects=("admin",),
            actions=("capability:invoke",),
            resources=("capability:*",),
            conditions=(cond,),
            priority=100,
            description="Deny admin access to all capabilities in prod",
        )
        assert r.effect is PolicyEffect.DENY
        assert "admin" in r.subjects
        assert cond in r.conditions

    def test_rule_is_frozen(self) -> None:
        r = PolicyRule(id="r1", name="r", effect=PolicyEffect.ALLOW)
        import pydantic
        try:
            r.name = "changed"
            assert False
        except pydantic.ValidationError:
            pass


class TestPolicy:
    def test_minimal_policy(self) -> None:
        p = Policy(id="pol-1", name="test-policy")
        assert p.id == "pol-1"
        assert p.enabled is True
        assert p.rules == ()

    def test_policy_with_rules(self) -> None:
        r = PolicyRule(id="r1", name="r", effect=PolicyEffect.ALLOW)
        p = Policy(id="pol-2", name="test", rules=(r,), enabled=False)
        assert len(p.rules) == 1
        assert p.enabled is False

    def test_policy_is_frozen(self) -> None:
        p = Policy(id="p1", name="p")
        import pydantic
        try:
            p.name = "changed"
            assert False
        except pydantic.ValidationError:
            pass


class TestPolicyDecision:
    def test_default_decision(self) -> None:
        d = PolicyDecision(effect=PolicyEffect.DENY)
        assert d.effect is PolicyEffect.DENY
        assert d.matched_rules == ()
        assert d.explanation == ""

    def test_allow_decision(self) -> None:
        d = PolicyDecision(
            effect=PolicyEffect.ALLOW,
            matched_rules=("r1",),
            explanation="Allowed by rule-1",
        )
        assert d.matched_rules == ("r1",)
        assert "Allowed" in d.explanation

    def test_decision_is_frozen(self) -> None:
        d = PolicyDecision(effect=PolicyEffect.ALLOW)
        import pydantic
        try:
            d.effect = PolicyEffect.DENY
            assert False
        except pydantic.ValidationError:
            pass
