from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.policy.decision_point import CachedDecision, PDPDecision, PolicyDecisionPoint


class TestPolicyDecisionPoint:
    @pytest.fixture
    def pdp(self) -> PolicyDecisionPoint:
        return PolicyDecisionPoint()

    def test_evaluate_without_engine(self, pdp: PolicyDecisionPoint) -> None:
        decision = pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert decision.result == "deny"
        assert "no policy engine configured" in decision.reason

    def test_evaluate_with_engine(self, pdp: PolicyDecisionPoint) -> None:
        engine = MagicMock()
        engine.evaluate.return_value = "allow"
        pdp.set_policy_engine(engine)
        decision = pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert decision.result == "allow"

    def test_evaluate_caching(self, pdp: PolicyDecisionPoint) -> None:
        engine = MagicMock()
        engine.evaluate.return_value = "allow"
        pdp.set_policy_engine(engine)
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert engine.evaluate.call_count == 1

    def test_cache_invalidation(self, pdp: PolicyDecisionPoint) -> None:
        pdp.set_cache(enabled=True, ttl_seconds=0)
        engine = MagicMock()
        engine.evaluate.return_value = "allow"
        pdp.set_policy_engine(engine)
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert engine.evaluate.call_count == 2

    def test_clear_cache(self, pdp: PolicyDecisionPoint) -> None:
        engine = MagicMock()
        engine.evaluate.return_value = "allow"
        pdp.set_policy_engine(engine)
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        pdp.clear_cache()
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert engine.evaluate.call_count == 2

    def test_evaluate_bulk(self, pdp: PolicyDecisionPoint) -> None:
        decisions = pdp.evaluate_bulk(
            [
                ("doc:1", "read", "user1", {}),
                ("doc:2", "write", "user2", {}),
            ]
        )
        assert len(decisions) == 2

    def test_get_decisions(self, pdp: PolicyDecisionPoint) -> None:
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        pdp.evaluate(resource="doc:2", action="write", subject="user2")
        decisions = pdp.get_decisions()
        assert len(decisions) == 2

    def test_get_decisions_with_filter(self, pdp: PolicyDecisionPoint) -> None:
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        pdp.evaluate(resource="doc:2", action="write", subject="user2")
        decisions = pdp.get_decisions(resource="doc:1")
        assert len(decisions) == 1
        assert decisions[0].resource == "doc:1"

    def test_disable_cache(self, pdp: PolicyDecisionPoint) -> None:
        pdp.set_cache(enabled=False)
        assert pdp._cache_enabled is False

    def test_decision_count(self, pdp: PolicyDecisionPoint) -> None:
        pdp.evaluate(resource="doc:1", action="read", subject="user1")
        assert pdp.get_decision_count() == 1
