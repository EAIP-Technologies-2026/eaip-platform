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


class CapabilityCategory(StrEnum):
    """Functional category of a capability."""

    OPERATIONAL = "operational"
    INTELLIGENCE = "intelligence"
    GOVERNANCE = "governance"
    COLLABORATION = "collaboration"
    EXPERIENCE = "experience"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"


class OperationType(StrEnum):
    """Operation types supported by a capability."""

    READ = "read"
    QUERY = "query"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"


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

    # Identity
    name: NonEmptyStr = Field(description="Globally unique, dot-namespaced name.")
    title: NonEmptyStr = Field(description="Human-readable title.")
    description: str = Field(default="")
    version: NonEmptyStr = Field(default="0.0.1")
    status: CapabilityStatus = Field(default=CapabilityStatus.REGISTERED)
    capability_id: str = Field(default="", description="Explicit capability identifier or alias.")
    category: CapabilityCategory | str = Field(
        default=CapabilityCategory.OPERATIONAL,
        description="Functional category.",
    )

    # Ownership
    domain: str = Field(default="eaip", description="Business/platform domain.")
    owner: str = Field(default="platform", description="Owning team or component.")
    lifecycle_state: str = Field(
        default="active", description="Lifecycle state (active/preview/deprecated)."
    )

    # Discovery
    routes: tuple[str, ...] = Field(
        default=(), description="Frontend routes associated with capability."
    )
    navigation_references: tuple[str, ...] = Field(default=(), description="Navigation item IDs.")
    api_operations: tuple[str, ...] = Field(
        default=(), description="Backend API operations (e.g. GET /api/v1/...)."
    )
    events: tuple[str, ...] = Field(
        default=(), description="Domain event names emitted or handled."
    )
    entities: tuple[str, ...] = Field(default=(), description="Domain entity types managed.")

    # Experience
    assistant_description: str = Field(default="", description="Assistant semantic description.")
    tour_metadata: dict[str, str] = Field(default_factory=dict, description="Tour step metadata.")
    search_terms: tuple[str, ...] = Field(default=(), description="Search index keywords.")
    documentation_references: tuple[str, ...] = Field(
        default=(), description="Documentation paths."
    )

    # Relationships
    parent_capability: str | None = Field(default=None, description="Parent capability ID.")
    child_capabilities: tuple[str, ...] = Field(default=(), description="Child capability IDs.")
    related_capabilities: tuple[str, ...] = Field(default=(), description="Related capability IDs.")
    depends_on: tuple[CapabilityDependency, ...] = Field(
        default=(),
        description="Capabilities this capability depends on.",
    )
    provides: tuple[str, ...] = Field(
        default=(),
        description="Interface or trait names this capability implements.",
    )

    # Operations
    supported_operations: tuple[OperationType, ...] = Field(
        default=(OperationType.READ,),
        description="Metadata describing operation types supported.",
    )

    # Contract & Metadata
    tags: tuple[str, ...] = Field(default=())
    contract: CapabilityContract | None = Field(
        default=None,
        description="Versioned contract with event-schema fingerprints.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata for tooling / dashboards.",
    )

    def id_or_name(self: Self) -> str:
        """Return explicit capability_id if set, else name."""
        return self.capability_id or self.name

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


__all__ = [
    "Capability",
    "CapabilityCategory",
    "CapabilityContract",
    "CapabilityDependency",
    "CapabilityStatus",
    "OperationType",
]
