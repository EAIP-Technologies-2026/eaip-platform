"""Registry of :class:`Capability` records, with helpers for enable/disable."""

from __future__ import annotations

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.exceptions.domain import NotFoundError
from eaip.registry.registry import Registry


class CapabilityRegistry:
    """High-level wrapper around :class:`Registry` for capabilities."""

    def __init__(self) -> None:
        self._inner: Registry[Capability] = Registry(
            name="capabilities", value_type=Capability
        )

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, capability: Capability, *, replace: bool = False) -> None:
        self._inner.register(capability.name, capability, replace=replace)

    def unregister(self, name: str) -> bool:
        return self._inner.unregister(name)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get(self, name: str) -> Capability:
        return self._inner.get(name)

    def has(self, name: str) -> bool:
        return self._inner.has(name)

    def all(self) -> list[Capability]:
        return self._inner.values()

    def enabled(self) -> list[Capability]:
        return [c for c in self._inner.values() if c.status is CapabilityStatus.ENABLED]

    # ------------------------------------------------------------------
    # Status transitions (replaces the record because Capability is frozen)
    # ------------------------------------------------------------------
    def set_status(self, name: str, status: CapabilityStatus) -> Capability:
        try:
            current = self._inner.get(name)
        except NotFoundError:
            raise
        updated = current.model_copy(update={"status": status})
        self._inner.register(name, updated, replace=True)
        return updated

    def enable(self, name: str) -> Capability:
        return self.set_status(name, CapabilityStatus.ENABLED)

    def disable(self, name: str) -> Capability:
        return self.set_status(name, CapabilityStatus.DISABLED)

    def deprecate(self, name: str) -> Capability:
        return self.set_status(name, CapabilityStatus.DEPRECATED)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._inner)

    def __contains__(self, name: str) -> bool:
        return name in self._inner


__all__ = ["CapabilityRegistry"]
