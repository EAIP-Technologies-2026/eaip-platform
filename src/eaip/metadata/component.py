"""Self-describing metadata attached to every registered component."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.types import NonEmptyStr


class ComponentKind(StrEnum):
    """Coarse taxonomy used to group components in registries and dashboards."""

    SERVICE = "service"
    ADAPTER = "adapter"
    PLUGIN = "plugin"
    CAPABILITY = "capability"
    INFRASTRUCTURE = "infrastructure"
    UTILITY = "utility"


class ComponentMetadata(BaseModel):
    """Immutable descriptor of a component.

    Every registered service, plugin, capability, and adapter is expected to
    advertise its own :class:`ComponentMetadata` so that the platform can
    introspect what is loaded, in what version, and at what stability level.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr = Field(description="Human-readable name (unique per registry).")
    kind: ComponentKind
    version: NonEmptyStr = Field(description="Semantic version of the component.")
    description: str = Field(default="", description="Optional one-line description.")
    vendor: str = Field(default="eaip", description="Originating vendor / namespace.")
    stability: str = Field(
        default="experimental",
        description="One of: experimental | beta | stable | deprecated.",
    )
    tags: tuple[str, ...] = Field(default=(), description="Free-form tags.")

    def is_stable(self) -> bool:
        """Determines if the component is in a stable state.

        Returns:
            True if the stability is 'stable', False otherwise.
        """
        return self.stability == "stable"


__all__ = ["ComponentKind", "ComponentMetadata"]
