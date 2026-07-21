"""Rate-limit policy engine — sliding-window counter with burst support."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from eaip.apiext.events import RateLimitApplied, RateLimitExceeded as RateLimitExceededEvent
from eaip.apiext.exceptions import PolicyNotFoundError
from eaip.apiext.models import RateLimitPolicy
from eaip.logging.context import get_logger


class _SlidingWindowCounter:
    """Tracks request timestamps for a single key within a sliding window."""

    __slots__ = ("_timestamps",)

    def __init__(self) -> None:
        """Initialize the counter with an empty timestamp store."""
        self._timestamps: list[float] = []

    def prune(self, window_seconds: float) -> None:
        """Remove timestamps outside the window."""
        cutoff = time.monotonic() - window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def count(self, window_seconds: float) -> int:
        """Return the number of requests within the window."""
        self.prune(window_seconds)
        return len(self._timestamps)

    def add(self) -> None:
        """Record a new request timestamp."""
        self._timestamps.append(time.monotonic())


class RateLimitPolicyEngine:
    """Manages rate-limit policies and enforces them via sliding-window counters."""

    def __init__(self) -> None:
        """Initialize the engine with empty policy registry and counters."""
        self._policies: dict[str, RateLimitPolicy] = {}
        self._counters: dict[str, _SlidingWindowCounter] = defaultdict(
            _SlidingWindowCounter,
        )
        self._log = get_logger("eaip.apiext.ratelimit")

    def create_policy(self, policy: RateLimitPolicy) -> RateLimitPolicy:
        """Create a new rate-limit policy.

        Args:
            policy: The policy definition.

        Returns:
            The created policy.

        Raises:
            ValueError: If a policy with the same id already exists.
        """
        if policy.id in self._policies:
            raise ValueError(f"Policy '{policy.id}' already exists.")
        self._policies[policy.id] = policy
        self._log.info(
            "apiext.ratelimit.policy.created",
            policy_id=policy.id,
            policy_name=policy.name,
        )
        from eaip.apiext.events import PolicyCreated

        PolicyCreated(
            policy_id=policy.id,
            policy_name=policy.name,
            policy_type="rate_limit",
        )
        return policy

    def update_policy(self, policy_id: str, updates: dict[str, Any]) -> RateLimitPolicy:
        """Update an existing rate-limit policy.

        Args:
            policy_id: The policy identifier.
            updates: Fields to update.

        Returns:
            The updated policy.

        Raises:
            PolicyNotFoundError: If the policy is not found.
        """
        existing = self._policies.get(policy_id)
        if existing is None:
            raise PolicyNotFoundError(
                f"Policy '{policy_id}' not found.",
                context={"policy_id": policy_id},
            )
        updated = existing.model_copy(update=updates)
        self._policies[policy_id] = updated
        from eaip.apiext.events import PolicyUpdated

        PolicyUpdated(
            policy_id=updated.id,
            policy_name=updated.name,
            policy_type="rate_limit",
        )
        return updated

    def delete_policy(self, policy_id: str) -> None:
        """Delete a rate-limit policy.

        Args:
            policy_id: The policy identifier.

        Raises:
            PolicyNotFoundError: If the policy is not found.
        """
        if policy_id not in self._policies:
            raise PolicyNotFoundError(
                f"Policy '{policy_id}' not found.",
                context={"policy_id": policy_id},
            )
        del self._policies[policy_id]
        # Clear associated counters
        keys_to_delete = [k for k in self._counters if k.startswith(policy_id)]
        for k in keys_to_delete:
            del self._counters[k]

    def list_policies(self) -> list[RateLimitPolicy]:
        """Return all registered policies.

        Returns:
            A list of all policies.
        """
        return list(self._policies.values())

    def get_policy(self, policy_id: str) -> RateLimitPolicy | None:
        """Look up a policy by identifier.

        Args:
            policy_id: The policy identifier.

        Returns:
            The matching policy, or ``None``.
        """
        return self._policies.get(policy_id)

    async def check_rate_limit(
        self,
        key: str,
        policy: RateLimitPolicy,
    ) -> tuple[bool, int, float]:
        """Check whether *key* is allowed under *policy*.

        Args:
            key: The rate-limit key (e.g. ``"user:42:/api/data"``).
            policy: The policy to apply.

        Returns:
            A tuple of ``(allowed, remaining, reset_at)``.
        """
        counter = self._counters[key]

        # Check burst allowance first
        burst_limit = int(policy.max_requests * policy.burst_multiplier)
        current_count = counter.count(policy.window_seconds)

        if current_count >= burst_limit:
            reset_at = time.monotonic() + policy.window_seconds
            RateLimitExceededEvent(
                policy_id=policy.id,
                policy_name=policy.name,
                key=key,
                max_requests=policy.max_requests,
                window_seconds=policy.window_seconds,
                reset_at=reset_at,
            )
            return False, 0, reset_at

        counter.add()
        new_count = counter.count(policy.window_seconds)
        remaining = max(0, policy.max_requests - new_count)
        reset_at = time.monotonic() + policy.window_seconds

        RateLimitApplied(
            policy_id=policy.id,
            policy_name=policy.name,
            key=key,
            max_requests=policy.max_requests,
            window_seconds=policy.window_seconds,
            remaining=remaining,
            reset_at=reset_at,
        )

        return True, remaining, reset_at

    def get_rate_limit_headers(
        self,
        key: str,
        policy: RateLimitPolicy,
    ) -> dict[str, str]:
        """Return rate-limit headers for *key* under *policy*.

        Args:
            key: The rate-limit key.
            policy: The policy to apply.

        Returns:
            A dict of rate-limit headers.
        """
        counter = self._counters.get(key)
        current_count = counter.count(policy.window_seconds) if counter else 0
        remaining = max(0, policy.max_requests - current_count)
        reset_at = time.time() + policy.window_seconds

        return {
            "X-RateLimit-Limit": str(policy.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_at)),
        }


__all__ = ["RateLimitPolicyEngine"]
