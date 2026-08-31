"""Role-Aware Assistant Context — Phase 5 composition layer.

Composes the authoritative A1001-A1003 permission/registry/graph services
(and optionally A1007 operational intelligence) into a single tenant-bound,
permission-aware, route-aware, operationally-fresh context that the
Enterprise Assistant uses to answer and act.

This module deliberately creates no new authorities: capability access,
approval requirements, and tenant isolation all come from
:class:`PermissionContextResolver`; capability metadata comes from the
canonical :class:`CapabilityRegistry`; platform topology comes from the
:class:`PlatformKnowledgeService`; live state comes from
:class:`OperationalIntelligenceService`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.capabilities.capability import OperationType
from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_context import IdentityScope, PermissionAwareContext
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.models import RiskTier
from eaip.copilot.operational_intelligence import (
    LiveOperationalSnapshot,
    OperationalIntelligenceService,
)
from eaip.kgraph.platform_graph import PlatformKnowledgeService
from eaip.shared.time import utc_now

_MIN_ROUTE_PARTS = 2


class AssistantAction(BaseModel):
    """A derived, authorized action available to the identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_name: str = Field(description="Dot-namespaced capability name.")
    operation: OperationType = Field(description="Authorized operation type.")
    requires_approval: bool = Field(
        default=False, description="Whether execution requires human approval."
    )
    risk: RiskTier = Field(default=RiskTier.INFORMATIONAL, description="Display risk annotation.")


class ActiveEntityContext(BaseModel):
    """Active entity and view context from the frontend application."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: str | None = Field(default=None, description="Active entity ID.")
    entity_type: str | None = Field(
        default=None,
        description="Active entity type (e.g. agent, workflow, brain, mission).",
    )
    active_tab: str | None = Field(default=None, description="Active tab in the page view.")
    selected_ids: tuple[str, ...] = Field(
        default=(), description="IDs of currently selected items."
    )
    page_context: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary sanitized page metadata."
    )


class RoleAwareAssistantContext(BaseModel):
    """The composed permission-aware, route-aware assistant context.

    All capability lists are derived from the authoritative permission-aware
    context, never from a manually maintained second catalogue.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: IdentityScope = Field(description="Authenticated identity scope.")
    permission_aware: PermissionAwareContext = Field(
        description="Raw authoritative permission-aware context for deeper checks."
    )
    tenant_id: str = Field(description="Effective tenant boundary.")
    organization_id: str = Field(default="", description="Organizational unit.")
    teams: tuple[str, ...] = Field(default=(), description="Assigned teams.")
    roles: tuple[str, ...] = Field(default=(), description="Effective roles.")

    current_route: str = Field(default="/", description="Active frontend route.")
    active_entity: ActiveEntityContext = Field(
        default_factory=ActiveEntityContext, description="Active entity and view context."
    )
    current_capabilities: tuple[str, ...] = Field(
        default=(), description="Route-matched capability names."
    )

    visible_capabilities: tuple[str, ...] = Field(default=(), description="Visible capabilities.")
    discoverable_capabilities: tuple[str, ...] = Field(
        default=(), description="Discoverable capabilities."
    )
    readable_capabilities: tuple[str, ...] = Field(default=(), description="Readable capabilities.")
    executable_capabilities: tuple[str, ...] = Field(
        default=(), description="Executable capabilities."
    )
    mutable_capabilities: tuple[str, ...] = Field(default=(), description="Mutable capabilities.")
    approval_required_capabilities: tuple[str, ...] = Field(
        default=(), description="Capabilities whose actions require approval."
    )
    restricted_capabilities: tuple[str, ...] = Field(
        default=(), description="Capabilities restricted from this identity."
    )

    available_actions: tuple[AssistantAction, ...] = Field(
        default=(), description="Authorized operations derived from effective permissions."
    )
    platform_entities: tuple[str, ...] = Field(
        default=(), description="Knowledge-graph entities relevant to the current capability."
    )
    platform_topology: dict[str, Any] = Field(
        default_factory=dict, description="Permission-scoped topology slice."
    )

    operational: LiveOperationalSnapshot | None = Field(
        default=None, description="Live operational state with freshness markers."
    )
    created_at: datetime = Field(default_factory=utc_now)

    def can_act(self, capability_name: str) -> bool:
        """Check whether the identity may execute actions on a capability."""
        return self.permission_aware.can_act(capability_name)

    def requires_approval(self, capability_name: str) -> bool:
        """Check whether actions on a capability require human approval."""
        return self.permission_aware.requires_approval(capability_name)

    def is_restricted(self, capability_name: str) -> bool:
        """Check whether a capability is restricted from this identity."""
        return self.permission_aware.is_restricted(capability_name)


def risk_for_operation(operation: OperationType) -> RiskTier:
    """Map an operation to a display risk annotation consistent with A1005.

    This is presentation metadata only; the authoritative risk/approval
    decision always happens inside :class:`GovernedActionExecutor`.
    """
    if operation in (OperationType.DELETE, OperationType.CANCEL):
        return RiskTier.DESTRUCTIVE
    if operation in (
        OperationType.CREATE,
        OperationType.UPDATE,
        OperationType.EXECUTE,
        OperationType.PAUSE,
        OperationType.RESUME,
        OperationType.APPROVE,
    ):
        return RiskTier.ACTION
    return RiskTier.INFORMATIONAL


class RoleAwareContextBuilder:
    """Builds :class:`RoleAwareAssistantContext` from authoritative services."""

    def __init__(
        self,
        *,
        capability_registry: CapabilityRegistry,
        permission_resolver: PermissionContextResolver,
        knowledge_service: PlatformKnowledgeService | None = None,
        operational_intelligence: OperationalIntelligenceService | None = None,
    ) -> None:
        """Initialize the context builder.

        Args:
            capability_registry: Authoritative canonical capability registry.
            permission_resolver: Authoritative permission context resolver.
            knowledge_service: Optional platform knowledge graph service.
            operational_intelligence: Optional A1007 operational intelligence service.
        """
        self._registry = capability_registry
        self._resolver = permission_resolver
        self._knowledge = knowledge_service
        self._operational = operational_intelligence

    def _identity_from_user(self, user: dict[str, Any]) -> IdentityScope:
        user_id = str(user.get("user_id") or user.get("id") or "anonymous")
        tenant_id = str(user.get("tenant_id") or "default")
        roles = tuple(user.get("roles") or ())
        teams = tuple(user.get("teams") or ())
        return IdentityScope(
            user_id=user_id,
            tenant_id=tenant_id,
            organization_id=str(user.get("organization_id") or ""),
            roles=roles,
            teams=teams,
            attributes=user.get("attributes") or {},
            is_authenticated=bool(user.get("is_authenticated", True)),
        )

    def _route_capabilities(self, current_route: str) -> list[str]:
        matches = self._registry.find_by_route(current_route)
        if not matches and current_route not in ("", "/"):
            base_route = "/" + current_route.strip("/").split("/")[0]
            matches = self._registry.find_by_route(base_route)
        return [c.name for c in matches]

    def _derive_actions(
        self,
        perm_ctx: PermissionAwareContext,
        executable_names: tuple[str, ...],
    ) -> tuple[AssistantAction, ...]:
        actions: list[AssistantAction] = []
        for name in executable_names:
            access = perm_ctx.get_access(name)
            cap = self._registry.try_get(name)
            if cap is None or access is None:
                continue
            operations = access.effective_operations or cap.supported_operations
            actions.extend(
                AssistantAction(
                    capability_name=name,
                    operation=op,
                    requires_approval=access.approval_required,
                    risk=risk_for_operation(op),
                )
                for op in operations
            )
        return tuple(actions)

    async def _platform_entities(
        self, capability_names: tuple[str, ...], context: PermissionAwareContext | None = None
    ) -> tuple[str, ...]:
        if self._knowledge is None or not capability_names:
            return ()
        entities: list[str] = []
        seen: set[str] = set()
        for name in capability_names:
            topo = await self._knowledge.get_capability_topology(name, context=context)
            if "error" in topo:
                continue
            for key in ("entities", "services", "dependencies"):
                for item in topo.get(key) or ():
                    label = getattr(item, "name", None) or getattr(item, "id", None) or str(item)
                    if label not in seen:
                        seen.add(label)
                        entities.append(label)
        return tuple(entities)

    def _infer_entity_context(
        self,
        current_route: str,
        entity_context: ActiveEntityContext | dict[str, Any] | None = None,
    ) -> ActiveEntityContext:
        """Infer or sanitize entity context from explicit input and route."""
        if isinstance(entity_context, ActiveEntityContext):
            ctx_dict = entity_context.model_dump()
        elif isinstance(entity_context, dict):
            ctx_dict = dict(entity_context)
        else:
            ctx_dict = {}

        entity_id = ctx_dict.get("entity_id")
        entity_type = ctx_dict.get("entity_type")
        active_tab = ctx_dict.get("active_tab")
        selected_ids = tuple(ctx_dict.get("selected_ids") or ())
        page_context = dict(ctx_dict.get("page_context") or {})

        # Route fallback inference: /agents/ag-123 -> entity_type='agent', entity_id='ag-123'
        if not entity_id or not entity_type:
            parts = [p for p in current_route.strip("/").split("/") if p]
            if len(parts) >= _MIN_ROUTE_PARTS:
                route_type_map = {
                    "agents": "agent",
                    "workflows": "workflow",
                    "brains": "brain",
                    "missions": "mission",
                    "incidents": "incident",
                    "memory": "memory",
                    "knowledge": "knowledge",
                }
                base = parts[0].lower()
                potential_id = parts[1]
                if base in route_type_map and potential_id and not potential_id.startswith("["):
                    entity_type = entity_type or route_type_map[base]
                    entity_id = entity_id or potential_id

        return ActiveEntityContext(
            entity_id=str(entity_id) if entity_id else None,
            entity_type=str(entity_type) if entity_type else None,
            active_tab=str(active_tab) if active_tab else None,
            selected_ids=selected_ids,
            page_context=page_context,
        )

    async def build(
        self,
        user: dict[str, Any],
        current_route: str = "/",
        *,
        entity_context: ActiveEntityContext | dict[str, Any] | None = None,
        include_operational: bool = True,
    ) -> RoleAwareAssistantContext:
        """Compose the full role-aware context for an identity on a route.

        Args:
            user: Authenticated caller claims.
            current_route: Active frontend route.
            entity_context: Optional active entity / view context.
            include_operational: Whether to attach a live operational snapshot.

        Returns:
            A composed, tenant-bound RoleAwareAssistantContext.
        """
        identity = self._identity_from_user(user)
        perm_ctx = self._resolver.resolve_context(identity)

        active_entity = self._infer_entity_context(current_route, entity_context)
        route_caps = tuple(self._route_capabilities(current_route))

        visible = tuple(perm_ctx.visible_capability_ids)
        executable = tuple(perm_ctx.executable_capability_ids)
        restricted = tuple(perm_ctx.restricted_capability_ids)

        discoverable: list[str] = []
        readable: list[str] = []
        mutable: list[str] = []
        approval_required: list[str] = []
        for name, cap_ctx in perm_ctx.capabilities.items():
            access = cap_ctx.access
            if access.discoverable and not access.restricted:
                discoverable.append(name)
            if access.readable and not access.restricted:
                readable.append(name)
            if access.mutable and not access.restricted:
                mutable.append(name)
            if access.approval_required and not access.restricted:
                approval_required.append(name)

        actions = self._derive_actions(perm_ctx, executable)
        entities = await self._platform_entities(route_caps, context=perm_ctx)

        platform_topology: dict[str, Any] = {}
        if self._knowledge is not None:
            primary_cap = route_caps[0] if route_caps else None
            if not primary_cap and active_entity.entity_type:
                type_map = {
                    "agent": "eaip.agents",
                    "workflow": "eaip.workflows",
                    "brain": "eaip.brains",
                    "mission": "eaip.missions",
                }
                primary_cap = type_map.get(active_entity.entity_type)
            if primary_cap:
                topo = await self._knowledge.get_capability_topology(primary_cap, context=perm_ctx)
                if "error" not in topo:
                    platform_topology = topo

        operational: LiveOperationalSnapshot | None = None
        if include_operational and self._operational is not None:
            operational = await self._operational.get_live_snapshot(identity)

        return RoleAwareAssistantContext(
            identity=identity,
            permission_aware=perm_ctx,
            tenant_id=identity.tenant_id,
            organization_id=identity.organization_id,
            teams=identity.teams,
            roles=identity.roles,
            current_route=current_route,
            active_entity=active_entity,
            current_capabilities=route_caps,
            visible_capabilities=visible,
            discoverable_capabilities=tuple(discoverable),
            readable_capabilities=tuple(readable),
            executable_capabilities=executable,
            mutable_capabilities=tuple(mutable),
            approval_required_capabilities=tuple(approval_required),
            restricted_capabilities=restricted,
            available_actions=actions,
            platform_entities=entities,
            platform_topology=platform_topology,
            operational=operational,
        )


__all__ = [
    "ActiveEntityContext",
    "AssistantAction",
    "RiskTier",
    "RoleAwareAssistantContext",
    "RoleAwareContextBuilder",
    "risk_for_operation",
]
