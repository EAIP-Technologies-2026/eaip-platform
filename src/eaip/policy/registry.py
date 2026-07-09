"""PolicyRegistry — an observable registry of policies."""

from __future__ import annotations

from collections.abc import Callable

from eaip.policy.models import Policy
from eaip.registry.registry import Observer, Registry


class PolicyRegistry:
    """Wraps a generic Registry[Policy] with policy-specific helpers."""

    def __init__(self) -> None:
        """Initialize the PolicyRegistry."""
        self._inner: Registry[Policy] = Registry(name="policies", value_type=Policy)

    def register(self, policy: Policy, *, replace: bool = False) -> None:
        """Register a policy.

        Args:
            policy: The policy to register.
            replace: If True, replace an existing policy with the same ID.
        """
        self._inner.register(policy.id, policy, replace=replace)

    def unregister(self, policy_id: str) -> bool:
        """Remove a policy by ID.

        Args:
            policy_id: The ID of the policy to remove.

        Returns:
            True if the policy existed, False otherwise.
        """
        return self._inner.unregister(policy_id)

    def get(self, policy_id: str) -> Policy:
        """Get a policy by ID.

        Args:
            policy_id: The ID of the policy.

        Returns:
            The policy.

        Raises:
            NotFoundError: If the policy is not in the registry.
        """
        return self._inner.get(policy_id)

    def try_get(self, policy_id: str) -> Policy | None:
        """Get a policy by ID, or None if not found.

        Args:
            policy_id: The ID of the policy.

        Returns:
            The policy, or None.
        """
        return self._inner.try_get(policy_id)

    def all(self) -> list[Policy]:
        """Return all registered policies."""
        return self._inner.values()

    def enabled(self) -> list[Policy]:
        """Return only enabled policies."""
        return [p for p in self._inner.values() if p.enabled]

    def clear(self) -> None:
        """Remove all policies from the registry."""
        self._inner.clear()

    def observe(self, observer: Observer[Policy]) -> Callable[[], None]:
        """Register an observer for registry changes."""
        return self._inner.observe(observer)

    def __len__(self) -> int:
        """Return the number of registered policies."""
        return len(self._inner)

    def __contains__(self, policy_id: str) -> bool:
        """Check if a policy ID is registered."""
        return policy_id in self._inner


__all__ = ["PolicyRegistry"]
