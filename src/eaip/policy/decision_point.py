"""Policy Decision Point — centralized PDP with caching, bulk evaluation, decision logs."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class PDPDecision:
    def __init__(
        self,
        request_id: str,
        resource: str,
        action: str,
        subject: str,
        result: str,
        reason: str = "",
    ) -> None:
        self.request_id = request_id
        self.resource = resource
        self.action = action
        self.subject = subject
        self.result = result
        self.reason = reason
        self.timestamp = utc_now()


class CachedDecision:
    def __init__(self, result: str, reason: str, ttl_seconds: int = 60) -> None:
        self.result = result
        self.reason = reason
        self.expires_at = utc_now() + timedelta(seconds=ttl_seconds)

    def is_valid(self) -> bool:
        return utc_now() < self.expires_at


class PolicyDecisionPoint:
    def __init__(self, policy_engine: Any = None, event_bus: Any = None) -> None:
        self._engine = policy_engine
        self._event_bus = event_bus
        self._decisions: list[PDPDecision] = []
        self._cache: dict[str, CachedDecision] = {}
        self._cache_enabled: bool = True
        self._cache_ttl: int = 60
        self._log = get_logger("eaip.policy.decision_point")

    def set_policy_engine(self, engine: Any) -> None:
        self._engine = engine

    def evaluate(
        self, resource: str, action: str, subject: str, context: dict[str, Any] | None = None
    ) -> PDPDecision:
        request_id = f"req-{len(self._decisions) + 1}"
        cache_key = f"{resource}:{action}:{subject}"

        if self._cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached.is_valid():
                decision = PDPDecision(
                    request_id, resource, action, subject, cached.result, cached.reason
                )
                self._decisions.append(decision)
                return decision

        if self._engine is not None:
            result = self._engine.evaluate(
                resource=resource, action=action, subject=subject, context=context or {}
            )
            result_str = str(result)
            reason = ""
        else:
            result_str = "deny"
            reason = "no policy engine configured"

        decision = PDPDecision(request_id, resource, action, subject, result_str, reason)
        self._decisions.append(decision)

        if self._cache_enabled:
            self._cache[cache_key] = CachedDecision(result_str, reason, self._cache_ttl)

        self._log.info("pdp.evaluate", resource=resource, action=action, result=result_str)
        return decision

    def evaluate_bulk(
        self, requests: list[tuple[str, str, str, dict[str, Any]]]
    ) -> list[PDPDecision]:
        return [self.evaluate(r, a, s, c) for r, a, s, c in requests]

    def get_decisions(
        self, limit: int = 100, offset: int = 0, resource: str | None = None
    ) -> list[PDPDecision]:
        results = list(self._decisions)
        if resource:
            results = [d for d in results if d.resource == resource]
        return results[offset : offset + limit]

    def get_decision_count(self) -> int:
        return len(self._decisions)

    def clear_cache(self) -> None:
        self._cache.clear()

    def set_cache(self, enabled: bool, ttl_seconds: int = 60) -> None:
        self._cache_enabled = enabled
        self._cache_ttl = ttl_seconds
        if not enabled:
            self._cache.clear()


__all__ = [
    "CachedDecision",
    "PDPDecision",
    "PolicyDecisionPoint",
]
