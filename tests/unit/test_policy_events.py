from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.policy.events import PolicyEvaluated, PolicyRuleMatched, PolicyViolation


class TestPolicyEvents:
    def test_policy_evaluated_event(self) -> None:
        evt = PolicyEvaluated(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
            effect="allow",
            matched_rules=("rule-1",),
        )
        assert evt.event_type == "eaip.policy.evaluated"
        assert isinstance(evt, DomainEvent)
        assert evt.subject_id == "user-1"

    def test_policy_violation_event(self) -> None:
        evt = PolicyViolation(
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:admin.delete",
            matched_rules=("deny-rule-1",),
            explanation="Denied by admin policy",
        )
        assert evt.event_type == "eaip.policy.violation"
        assert "admin" in evt.explanation

    def test_policy_rule_matched_event(self) -> None:
        evt = PolicyRuleMatched(
            rule_id="rule-42",
            rule_name="Allow Agent Run",
            effect="allow",
            subject_id="user-1",
            action="capability:invoke",
            resource="capability:agent.run",
        )
        assert evt.event_type == "eaip.policy.rule_matched"
        assert evt.rule_id == "rule-42"
