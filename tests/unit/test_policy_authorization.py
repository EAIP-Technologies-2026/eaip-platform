from __future__ import annotations

from eaip.events.bus import EventBus
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.events import PolicyEvaluated, PolicyViolation
from eaip.policy.exceptions import PolicyViolationError
from eaip.policy.models import Policy, PolicyDecision, PolicyEffect, PolicyRule
from eaip.policy.registry import PolicyRegistry


def _policy(pid: str = "pol-1", rules: tuple = (), enabled: bool = True) -> Policy:
    return Policy(id=pid, name=pid, rules=rules, enabled=enabled)


def _rule(
    rid: str = "r1",
    effect: PolicyEffect = PolicyEffect.ALLOW,
    subjects: tuple[str, ...] = (),
    actions: tuple[str, ...] = (),
    resources: tuple[str, ...] = (),
) -> PolicyRule:
    return PolicyRule(id=rid, name=rid, effect=effect, subjects=subjects, actions=actions, resources=resources)


def _ctx(
    sid: str = "user-1",
    roles: tuple[str, ...] = (),
    action: str = "read",
    resource: str = "file",
) -> PolicyEvaluationContext:
    return PolicyEvaluationContext(subject_id=sid, subject_roles=roles, action=action, resource=resource)


class TestAuthorizationManager:
    def test_check_permission_allow(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.ALLOW)
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        decision = auth.check_permission(_ctx())
        assert decision.effect is PolicyEffect.ALLOW

    def test_check_permission_deny(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.DENY)
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        decision = auth.check_permission(_ctx())
        assert decision.effect is PolicyEffect.DENY

    def test_authorize_allow_passes(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.ALLOW)
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        auth.authorize(_ctx())

    def test_authorize_deny_raises(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.DENY)
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        try:
            auth.authorize(_ctx())
            assert False, "expected PolicyViolationError"
        except PolicyViolationError:
            pass

    def test_authorize_capability(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.ALLOW, actions=("capability:invoke",), resources=("capability:agent.run",))
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        auth.authorize_capability("capability:agent.run", _ctx())

    def test_authorize_capability_denied(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.DENY, actions=("capability:invoke",), resources=("capability:admin.*",))
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry)
        try:
            auth.authorize_capability("capability:admin.delete", _ctx())
            assert False, "expected PolicyViolationError"
        except PolicyViolationError:
            pass

    def test_events_published_on_deny(self) -> None:
        """Verify policy evaluation and violation events are published on deny."""
        import asyncio
        bus = EventBus()
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = _rule(effect=PolicyEffect.DENY)
        registry.register(_policy(rules=(rule,)))
        auth = AuthorizationManager(engine, registry, event_bus=bus)

        evaluated: list[PolicyEvaluated] = []
        violations: list[PolicyViolation] = []

        bus.subscribe(PolicyEvaluated, evaluated.append)
        bus.subscribe(PolicyViolation, violations.append)

        try:
            auth.authorize(_ctx())
        except PolicyViolationError:
            pass

        assert len(evaluated) > 0
        assert evaluated[0].effect == "deny"
        assert len(violations) > 0
