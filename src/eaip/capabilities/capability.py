"""A `Capability` is a self-describing unit of functionality the platform exposes.

Capabilities carry a versioned contract, dependency declarations, and
event-schema fingerprints so that consumers can discover, resolve, and
validate them at runtime.
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


class CapabilityDependency(BaseModel):
    """Declares a dependency on another capability."""

    name: NonEmptyStr = Field(description="Capability name this dependency targets.")
    version_spec: str = Field(
        default="*",
        description="Semver range spec (empty or '*' = any version).",
    )
    optional: bool = Field(default=False, description="If True, failure is a warning.")


class CapabilityContract(BaseModel):
    """Versioned contract that a capability advertises.

    Consumers bind to ``contract_version``, not the capability's implementation
    version. This allows the implementation to evolve independently as long as
    the contract remains backward-compatible.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: NonEmptyStr = Field(
        description="Semantic version of this contract.",
    )
    event_schemas: dict[str, str] = Field(
        default_factory=dict,
        description="Map of ``event_type -> schema_fingerprint`` for events this "
        "capability publishes or consumes.",
    )


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
    depends_on: tuple[CapabilityDependency, ...] = Field(
        default=(),
        description="Capabilities this capability depends on.",
    )
    provides: tuple[str, ...] = Field(
        default=(),
        description="Interface or trait names this capability implements.",
    )
    contract: CapabilityContract | None = Field(
        default=None,
        description="Versioned contract with event-schema fingerprints.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata for tooling / dashboards.",
    )

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


__all__ = ["Capability", "CapabilityContract", "CapabilityDependency", "CapabilityStatus"]
