"""End-to-end policy authorization demo.

Demonstrates:
  1. Creating a capability with RBAC policies
  2. Policy evaluation protecting a capability invocation
  3. Allow and deny scenarios
"""

from __future__ import annotations

from eaip.policy.authorization import AuthorizationManager
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.exceptions import PolicyViolationError
from eaip.policy.models import Policy, PolicyEffect, PolicyRule
from eaip.policy.registry import PolicyRegistry


class TestPolicyAuthorizationDemo:
    def test_capability_invocation_protected_by_policy(self) -> None:
        """Demonstrate policy evaluation protecting a capability invocation."""
        engine = PolicyEngine()
        registry = PolicyRegistry()

        deny_guest = PolicyRule(
            id="deny-guest",
            name="Deny Guest Users",
            effect=PolicyEffect.DENY,
            subjects=("guest",),
            actions=("capability:invoke",),
            resources=("capability:agent.run",),
            priority=100,
        )
        allow_admin = PolicyRule(
            id="allow-admin",
            name="Allow Admins",
            effect=PolicyEffect.ALLOW,
            subjects=("admin",),
            actions=("capability:invoke",),
            resources=("capability:agent.run",),
        )
        policy = Policy(
            id="cap-access",
            name="Capability Access Control",
            rules=(deny_guest, allow_admin),
        )
        registry.register(policy)

        auth = AuthorizationManager(engine, registry)

        guest_ctx = PolicyEvaluationContext(
            subject_id="guest-1",
            subject_roles=("guest",),
            action="capability:invoke",
            resource="capability:agent.run",
        )

        try:
            auth.authorize(guest_ctx)
            raise AssertionError("Guest should be denied")
        except PolicyViolationError as exc:
            assert "Denied" in str(exc)

        admin_ctx = PolicyEvaluationContext(
            subject_id="admin-1",
            subject_roles=("admin",),
            action="capability:invoke",
            resource="capability:agent.run",
        )
        auth.authorize(admin_ctx)

    def test_abac_protection_by_environment(self) -> None:
        """Demonstrate ABAC: deny production access unless MFA is enabled."""
        engine = PolicyEngine()
        registry = PolicyRegistry()

        from eaip.policy.models import ConditionOp, PolicyCondition

        require_mfa = PolicyRule(
            id="require-mfa",
            name="Require MFA in Production",
            effect=PolicyEffect.DENY,
            actions=("capability:invoke",),
            resources=("capability:*",),
            conditions=(
                PolicyCondition(attribute="env", operator=ConditionOp.EQ, value="prod"),
                PolicyCondition(attribute="mfa", operator=ConditionOp.NEQ, value=True),
            ),
            priority=100,
        )
        allow_all = PolicyRule(
            id="allow-all",
            name="Default Allow",
            effect=PolicyEffect.ALLOW,
        )
        policy = Policy(
            id="abac-mfa",
            name="ABAC MFA Policy",
            rules=(require_mfa, allow_all),
        )
        registry.register(policy)

        auth = AuthorizationManager(engine, registry)

        prod_no_mfa = PolicyEvaluationContext(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
            attributes={"env": "prod", "mfa": False},
        )
        try:
            auth.authorize(prod_no_mfa)
            raise AssertionError("Should be denied: prod without MFA")
        except PolicyViolationError:
            pass

        prod_with_mfa = PolicyEvaluationContext(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
            attributes={"env": "prod", "mfa": True},
        )
        auth.authorize(prod_with_mfa)

        dev_no_mfa = PolicyEvaluationContext(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
            attributes={"env": "dev", "mfa": False},
        )
        auth.authorize(dev_no_mfa)
