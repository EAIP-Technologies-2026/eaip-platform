"""Registry of :class:`Capability` records, with helpers for enable/disable."""

from __future__ import annotations

from typing import Self

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.exceptions.domain import NotFoundError
from eaip.registry.registry import Registry


class CapabilityRegistry:
    """High-level wrapper around :class:`Registry` for capabilities."""

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

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get(self: Self, name: str) -> Capability:
        """Get a capability by name.

        Args:
            name: The name of the capability to get.

        Returns:
            The capability.
        """
        return self._inner.get(name)

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
        """
        try:
            current = self._inner.get(name)
        except NotFoundError:
            raise
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
