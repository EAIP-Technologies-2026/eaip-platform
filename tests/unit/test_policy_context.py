from __future__ import annotations

from eaip.policy.context import PolicyEvaluationContext


class TestPolicyEvaluationContext:
    def test_minimal_context(self) -> None:
        ctx = PolicyEvaluationContext(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
        )
        assert ctx.subject_id == "user-1"
        assert ctx.subject_roles == ()
        assert ctx.attributes == {}

    def test_with_roles_and_attributes(self) -> None:
        ctx = PolicyEvaluationContext(
            subject_id="user-2",
            subject_roles=("admin", "operator"),
            action="capability:invoke",
            resource="capability:agent.run",
            attributes={"env": "prod", "tier": "critical"},
        )
        assert "admin" in ctx.subject_roles
        assert ctx.attributes["env"] == "prod"

    def test_context_is_frozen(self) -> None:
        ctx = PolicyEvaluationContext(
            subject_id="u1",
            action="read",
            resource="file",
        )
        import pydantic

        try:
            ctx.subject_id = "changed"
            raise AssertionError()
        except pydantic.ValidationError:
            pass

    def test_timestamp_is_set(self) -> None:
        ctx = PolicyEvaluationContext(
            subject_id="u1",
            action="read",
            resource="file",
        )
        assert ctx.timestamp is not None
