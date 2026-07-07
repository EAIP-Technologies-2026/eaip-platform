"""Identity-related protocols for components and entities."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from eaip.shared.identifiers import ComponentId


@runtime_checkable
class Identifiable(Protocol):
    """A component that exposes a stable :class:`ComponentId`."""

    @property
    def id(self) -> ComponentId:
        """Returns the component's identifier.

        Returns:
            The component's identifier.
        """
        ...


@runtime_checkable
class Named(Protocol):
    """A component that exposes a human-readable name."""

    @property
    def name(self) -> str:
        """Returns the human-readable name.

        Returns:
            The human-readable name.
        """
        ...


@runtime_checkable
class Versioned(Protocol):
    """A component that exposes a semantic version."""

    @property
    def version(self) -> str:
        """Returns the semantic version.

        Returns:
            The semantic version.
        """
        ...


__all__ = ["Identifiable", "Named", "Versioned"]
