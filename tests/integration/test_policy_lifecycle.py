"""Integration tests for the policy subsystem lifecycle."""

from __future__ import annotations

from eaip.policy.authorization import AuthorizationManager
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.models import Policy, PolicyEffect, PolicyRule
from eaip.policy.registry import PolicyRegistry


class TestPolicyLifecycle:
    async def test_policy_engine_integration(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = PolicyRule(id="r1", name="Allow All", effect=PolicyEffect.ALLOW)
        policy = Policy(id="p1", name="default-allow", rules=(rule,))
        registry.register(policy)

        ctx = PolicyEvaluationContext(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
        )

        decision = engine.evaluate(ctx, registry.enabled())
        assert decision.effect is PolicyEffect.ALLOW

    async def test_authorization_manager_with_registry(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()
        rule = PolicyRule(
            id="r1",
            name="Deny Admin Delete",
            effect=PolicyEffect.DENY,
            subjects=("admin",),
            actions=("capability:invoke",),
            resources=("capability:admin.*",),
        )
        policy = Policy(id="p1", name="admin-policy", rules=(rule,))
        registry.register(policy)

        auth = AuthorizationManager(engine, registry)

        ctx = PolicyEvaluationContext(
            subject_id="user-1",
            subject_roles=("admin",),
            action="capability:invoke",
            resource="capability:admin.delete",
        )

        from eaip.policy.exceptions import PolicyViolationError

        try:
            auth.authorize(ctx)
            raise AssertionError("expected PolicyViolationError")
        except PolicyViolationError:
            pass

    async def test_multiple_policies_resolved(self) -> None:
        engine = PolicyEngine()
        registry = PolicyRegistry()

        viewer = PolicyRule(
            id="v1",
            name="Viewer Read",
            effect=PolicyEffect.ALLOW,
            subjects=("viewer",),
            actions=("read",),
        )
        admin = PolicyRule(
            id="a1",
            name="Admin All",
            effect=PolicyEffect.ALLOW,
            subjects=("admin",),
            actions=("*",),
        )
        deny_dangerous = PolicyRule(
            id="d1",
            name="Deny Shutdown",
            effect=PolicyEffect.DENY,
            subjects=("admin",),
            actions=("capability:invoke",),
            resources=("capability:system.shutdown",),
            priority=100,
        )

        registry.register(Policy(id="viewer-pol", name="viewer", rules=(viewer,)))
        registry.register(Policy(id="admin-pol", name="admin", rules=(admin, deny_dangerous)))

        auth = AuthorizationManager(engine, registry)

        ctx_view = PolicyEvaluationContext(
            subject_id="u1",
            subject_roles=("viewer",),
            action="read",
            resource="file",
        )
        auth.authorize(ctx_view)

        ctx_admin_read = PolicyEvaluationContext(
            subject_id="u2",
            subject_roles=("admin",),
            action="read",
            resource="file",
        )
        auth.authorize(ctx_admin_read)

        ctx_shutdown = PolicyEvaluationContext(
            subject_id="u3",
            subject_roles=("admin",),
            action="capability:invoke",
            resource="capability:system.shutdown",
        )
        from eaip.policy.exceptions import PolicyViolationError

        try:
            auth.authorize(ctx_shutdown)
            raise AssertionError("expected PolicyViolationError")
        except PolicyViolationError:
            pass
