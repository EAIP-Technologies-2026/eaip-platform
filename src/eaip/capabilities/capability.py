"""A `Capability` is a self-describing unit of functionality the platform exposes.

Examples (delivered by future engineering packs): "agent.run", "tool.http",
"memory.vector". The Foundation only ships the descriptor and registry.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from eaip.metadata.component import ComponentKind, ComponentMetadata
from eaip.types import NonEmptyStr


class CapabilityStatus(StrEnum):
    """Lifecycle status of a registered capability."""

    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class Capability(BaseModel):
    """Immutable record describing a capability.

    Concrete implementations (handlers, factories) are registered elsewhere
    (DI container, plugin loader). A capability is the **public contract** —
    not the implementation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr = Field(description="Globally unique, dot-namespaced name.")
    title: NonEmptyStr = Field(description="Human-readable title.")
    description: str = Field(default="")
    version: NonEmptyStr = Field(default="0.0.1")
    status: CapabilityStatus = Field(default=CapabilityStatus.REGISTERED)
    tags: tuple[str, ...] = Field(default=())

    def to_metadata(self: Self) -> ComponentMetadata:
        """Convert the capability to metadata.

        Returns:
            The component metadata for this capability.
        """
        return ComponentMetadata(
            name=self.name,
            kind=ComponentKind.CAPABILITY,
            version=self.version,
            description=self.description,
            tags=self.tags,
            stability="stable" if self.status is CapabilityStatus.ENABLED else "experimental",
        )


__all__ = ["Capability", "CapabilityStatus"]
