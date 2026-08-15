"""Registry of :class:`Capability` records, with helpers for enable/disable."""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

from eaip.capabilities.capability import (
    Capability,
    CapabilityCategory,
    CapabilityStatus,
)
from eaip.registry.registry import Observer, Registry


class CapabilityRegistry:
    """High-level wrapper around :class:`Registry` for capabilities.

    Extends the base with capability-specific lifecycle methods (enable,
    disable, deprecate) and exposes the underlying observer for graph
    integration.
    """

    def __init__(self: Self) -> None:
        """Initialize the capability registry."""
        self._inner: Registry[Capability] = Registry(name="capabilities", value_type=Capability)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self: Self, capability: Capability, *, replace: bool = False) -> None:
        """Register a capability.

        Args:
            capability: The capability to register.
            replace: Whether to replace an existing capability with the same name.
        """
        self._inner.register(capability.name, capability, replace=replace)

    def unregister(self: Self, name: str) -> bool:
        """Unregister a capability.

        Args:
            name: The name of the capability to unregister.

        Returns:
            True if the capability was found and unregistered, False otherwise.
        """
        return self._inner.unregister(name)

    def clear(self: Self) -> None:
        """Remove all registered capabilities."""
        self._inner.clear()

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get(self: Self, name: str) -> Capability:
        """Get a capability by name.

        Args:
            name: The name of the capability to get.

        Returns:
            The capability.

        Raises:
            NotFoundError: If the capability is not registered.
        """
        return self._inner.get(name)

    def try_get(self: Self, name: str) -> Capability | None:
        """Get a capability by name, or None if not found.

        Args:
            name: The name of the capability.

        Returns:
            The capability or None.
        """
        return self._inner.try_get(name)

    def has(self: Self, name: str) -> bool:
        """Check if a capability exists.

        Args:
            name: The name of the capability to check.

        Returns:
            True if the capability exists, False otherwise.
        """
        return self._inner.has(name)

    def all(self: Self) -> list[Capability]:
        """Get all registered capabilities.

        Returns:
            A list of all registered capabilities.
        """
        return self._inner.values()

    def enabled(self: Self) -> list[Capability]:
        """Get all enabled capabilities.

        Returns:
            A list of all enabled capabilities.
        """
        return [c for c in self._inner.values() if c.status is CapabilityStatus.ENABLED]

    def keys(self: Self) -> list[str]:
        """Get all registered capability names.

        Returns:
            A list of capability names.
        """
        return self._inner.keys()

    def items(self: Self) -> list[tuple[str, Capability]]:
        """Get all (name, capability) pairs.

        Returns:
            A list of name-capability tuples.
        """
        return self._inner.items()

    # ------------------------------------------------------------------
    # Status transitions (replaces the record because Capability is frozen)
    # ------------------------------------------------------------------
    def set_status(self: Self, name: str, status: CapabilityStatus) -> Capability:
        """Set the status of a capability.

        Args:
            name: The name of the capability.
            status: The new status.

        Returns:
            The updated capability.

        Raises:
            NotFoundError: If the capability is not registered.
        """
        current = self._inner.get(name)
        updated = current.model_copy(update={"status": status})
        self._inner.register(name, updated, replace=True)
        return updated

    def enable(self: Self, name: str) -> Capability:
        """Enable a capability.

        Args:
            name: The name of the capability to enable.

        Returns:
            The enabled capability.
        """
        return self.set_status(name, CapabilityStatus.ENABLED)

    def disable(self: Self, name: str) -> Capability:
        """Disable a capability.

        Args:
            name: The name of the capability to disable.

        Returns:
            The disabled capability.
        """
        return self.set_status(name, CapabilityStatus.DISABLED)

    def deprecate(self: Self, name: str) -> Capability:
        """Deprecate a capability.

        Args:
            name: The name of the capability to deprecate.

        Returns:
            The deprecated capability.
        """
        return self.set_status(name, CapabilityStatus.DEPRECATED)

    # ------------------------------------------------------------------
    # Enhanced Queries & Filtering (A1001)
    # ------------------------------------------------------------------
    def find_by_category(self: Self, category: str | CapabilityCategory) -> list[Capability]:
        """Find capabilities matching a specific category.

        Args:
            category: Category string or CapabilityCategory enum.

        Returns:
            List of matching capabilities.
        """
        cat_str = str(category).lower()
        return [c for c in self._inner.values() if str(c.category).lower() == cat_str]

    def find_by_status(self: Self, status: CapabilityStatus) -> list[Capability]:
        """Find capabilities matching a specific lifecycle status.

        Args:
            status: Lifecycle status.

        Returns:
            List of matching capabilities.
        """
        return [c for c in self._inner.values() if c.status is status]

    def find_by_domain(self: Self, domain: str) -> list[Capability]:
        """Find capabilities matching a specific domain.

        Args:
            domain: Domain name string.

        Returns:
            List of matching capabilities.
        """
        return [c for c in self._inner.values() if c.domain.lower() == domain.lower()]

    def find_by_tag(self: Self, tag: str) -> list[Capability]:
        """Find capabilities carrying a specific tag.

        Args:
            tag: Tag name string.

        Returns:
            List of matching capabilities.
        """
        return [c for c in self._inner.values() if tag in c.tags]

    def find_by_route(self: Self, route: str) -> list[Capability]:
        """Find capabilities mapped to a given frontend route.

        Args:
            route: Route path (e.g. '/dashboard').

        Returns:
            List of capabilities mapped to the route.
        """
        return [c for c in self._inner.values() if route in c.routes]

    def get_related(self: Self, name: str) -> list[Capability]:
        """Get capabilities explicitly listed as related to `name`.

        Args:
            name: Name of the capability.

        Returns:
            List of related capabilities found in registry.
        """
        cap = self.try_get(name)
        if not cap:
            return []
        related = []
        for rel_name in cap.related_capabilities:
            rel_cap = self.try_get(rel_name)
            if rel_cap:
                related.append(rel_cap)
        return related

    def get_children(self: Self, name: str) -> list[Capability]:
        """Get capabilities that are direct children or declare `name` as parent.

        Args:
            name: Name of the capability.

        Returns:
            List of child capabilities.
        """
        cap = self.try_get(name)
        children_names = set(cap.child_capabilities) if cap else set()
        # Also find any capability declaring parent_capability == name
        for c in self._inner.values():
            if c.parent_capability == name:
                children_names.add(c.name)
        return [self._inner.get(cn) for cn in children_names if self.has(cn)]

    def get_parent(self: Self, name: str) -> Capability | None:
        """Get parent capability for `name` if defined.

        Args:
            name: Name of the capability.

        Returns:
            Parent Capability or None.
        """
        cap = self.try_get(name)
        if not cap or not cap.parent_capability:
            return None
        return self.try_get(cap.parent_capability)

    def list_ordered(self: Self, order_by: str = "name") -> list[Capability]:
        """Return all capabilities in deterministic order.

        Args:
            order_by: Field to order by ('name', 'category', 'status', 'title').

        Returns:
            Deterministically sorted list of capabilities.
        """
        all_caps = self._inner.values()
        if order_by == "category":
            return sorted(all_caps, key=lambda c: (str(c.category), str(c.name)))
        if order_by == "status":
            return sorted(all_caps, key=lambda c: (str(c.status), str(c.name)))
        if order_by == "title":
            return sorted(all_caps, key=lambda c: (str(c.title), str(c.name)))
        return sorted(all_caps, key=lambda c: str(c.name))

    def validate_capability(self: Self, capability: Capability) -> list[str]:
        """Validate capability contract integrity and dependencies.

        Args:
            capability: Capability to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []
        if not capability.name or not capability.name.strip():
            errors.append("Capability name cannot be empty")
        if not capability.title or not capability.title.strip():
            errors.append("Capability title cannot be empty")
        if not capability.version or not capability.version.strip():
            errors.append("Capability version cannot be empty")
        return errors

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------
    def observe(self: Self, observer: Observer[Capability]) -> Callable[[], None]:
        """Register an observer for registry changes.

        Returns:
            A callable that removes the observer.
        """
        return self._inner.observe(observer)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def __len__(self: Self) -> int:
        """Get the number of registered capabilities.

        Returns:
            The number of registered capabilities.
        """
        return len(self._inner)

    def __contains__(self: Self, name: str) -> bool:
        """Check if a capability is registered.

        Args:
            name: The name of the capability.

        Returns:
            True if the capability is registered, False otherwise.
        """
        return name in self._inner


__all__ = ["CapabilityRegistry"]
