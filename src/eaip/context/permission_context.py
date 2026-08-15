"""Permission-Aware Context domain models.

Defines the contract for representing an authenticated identity's effective
permissions, visible capabilities, and actionable authority across tenant boundaries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.capabilities.capability import OperationType
from eaip.shared.time import utc_now


class IdentityScope(BaseModel):
    """Authenticated user, tenant, and organizational identity representation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str = Field(description="Unique subject/user identifier.")
    tenant_id: str = Field(description="Tenant boundary identifier.")
    organization_id: str = Field(default="", description="Organizational unit identifier.")
    roles: tuple[str, ...] = Field(default=(), description="Assigned RBAC role names.")
    teams: tuple[str, ...] = Field(default=(), description="Assigned team identifiers.")
    attributes: dict[str, Any] = Field(default_factory=dict, description="ABAC subject attributes.")
    is_authenticated: bool = Field(default=True, description="Whether identity is authenticated.")


class CapabilityAccessLevel(BaseModel):
    """Effective access permissions for a specific capability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    visible: bool = Field(default=False, description="Whether capability appears in navigation and UI.")
    discoverable: bool = Field(default=False, description="Whether capability is discoverable via search and assistant.")
    readable: bool = Field(default=False, description="Whether entity details and telemetry can be viewed.")
    executable: bool = Field(default=False, description="Whether operations and workflows can be executed.")
    mutable: bool = Field(default=False, description="Whether resources can be created, edited, or deleted.")
    approval_required: bool = Field(default=False, description="Whether execution requires human approval.")
    restricted: bool = Field(default=False, description="Whether access is explicitly restricted/denied.")
    effective_operations: tuple[OperationType, ...] = Field(
        default=(),
        description="List of specific operations authorized for this identity.",
    )


class CapabilityPermissionContext(BaseModel):
    """Permission evaluation result for a single capability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str = Field(description="Unique capability identifier.")
    capability_name: str = Field(description="Dot-namespaced capability name.")
    access: CapabilityAccessLevel = Field(description="Effective access flags.")
    applicable_roles: tuple[str, ...] = Field(default=(), description="Roles granting or impacting access.")
    tenant_id: str = Field(description="Tenant boundary where evaluated.")


class PermissionAwareContext(BaseModel):
    """Permission-aware context representing an identity's authorized view of EAIP."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: IdentityScope = Field(description="Authenticated subject identity.")
    capabilities: dict[str, CapabilityPermissionContext] = Field(
        default_factory=dict,
        description="Map of capability_name -> CapabilityPermissionContext.",
    )
    visible_capability_ids: tuple[str, ...] = Field(
        default=(),
        description="IDs of capabilities the identity CAN SEE.",
    )
    executable_capability_ids: tuple[str, ...] = Field(
        default=(),
        description="IDs of capabilities the identity CAN ACT on.",
    )
    restricted_capability_ids: tuple[str, ...] = Field(
        default=(),
        description="IDs of capabilities explicitly restricted or hidden.",
    )
    created_at: datetime = Field(default_factory=utc_now)

    def can_see(self, capability_name: str) -> bool:
        """Check if identity can see the specified capability."""
        cap_ctx = self.capabilities.get(capability_name)
        return cap_ctx.access.visible if cap_ctx else False

    def can_act(self, capability_name: str) -> bool:
        """Check if identity can execute actions on the specified capability."""
        cap_ctx = self.capabilities.get(capability_name)
        return cap_ctx.access.executable if cap_ctx else False

    def requires_approval(self, capability_name: str) -> bool:
        """Check if actions on the capability require approval."""
        cap_ctx = self.capabilities.get(capability_name)
        return cap_ctx.access.approval_required if cap_ctx else False

    def is_restricted(self, capability_name: str) -> bool:
        """Check if capability is restricted from this identity."""
        cap_ctx = self.capabilities.get(capability_name)
        return cap_ctx.access.restricted if cap_ctx else True

    def get_access(self, capability_name: str) -> CapabilityAccessLevel | None:
        """Retrieve access level for a capability."""
        cap_ctx = self.capabilities.get(capability_name)
        return cap_ctx.access if cap_ctx else None


__all__ = [
    "CapabilityAccessLevel",
    "CapabilityPermissionContext",
    "IdentityScope",
    "PermissionAwareContext",
]
