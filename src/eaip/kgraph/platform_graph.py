"""Platform Knowledge / Experience Graph.

Constructs and queries the enterprise-wide knowledge graph representing
relationships between capabilities, routes, APIs, services, events, entities,
documentation, and user experiences.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_context import PermissionAwareContext
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.models import Entity, Relationship
from eaip.logging.context import get_logger


class PlatformNodeType(StrEnum):
    """Canonical node types for platform knowledge representation."""

    CAPABILITY = "capability"
    ROUTE = "route"
    API = "api"
    SERVICE = "service"
    EVENT = "event"
    ENTITY = "entity"
    DOCUMENTATION = "documentation"
    EXPERIENCE = "experience"
    ROLE = "role"


class PlatformEdgeType(StrEnum):
    """Canonical edge types connecting platform knowledge entities."""

    HAS_ROUTE = "HAS_ROUTE"
    EXPOSES_API = "EXPOSES_API"
    EMITS_EVENT = "EMITS_EVENT"
    USES_SERVICE = "USES_SERVICE"
    RELATES_TO_ENTITY = "RELATES_TO_ENTITY"
    HAS_DOCUMENTATION = "HAS_DOCUMENTATION"
    HAS_EXPERIENCE = "HAS_EXPERIENCE"
    DEPENDS_ON_CAPABILITY = "DEPENDS_ON_CAPABILITY"
    REQUIRES_ROLE = "REQUIRES_ROLE"


async def build_platform_knowledge_graph(  # noqa: PLR0912, PLR0915
    registry: CapabilityRegistry,
    graph: KnowledgeGraph | None = None,
) -> KnowledgeGraph:
    """Build a KnowledgeGraph populated with all platform capability relationships.

    Args:
        registry: Capability registry loaded with capabilities.
        graph: Optional existing KnowledgeGraph to populate.

    Returns:
        Populated KnowledgeGraph instance.
    """
    kg = graph if graph is not None else KnowledgeGraph()
    capabilities = registry.all()

    # Step 1: Add all capability nodes first
    for cap in capabilities:
        cap_entity_id = f"cap:{cap.name}"
        if (
            not kg.has_entity(cap_entity_id)
            if hasattr(kg, "has_entity")
            else cap_entity_id not in kg._entities
        ):
            await kg.add_entity(
                Entity(
                    id=cap_entity_id,
                    type=PlatformNodeType.CAPABILITY,
                    name=cap.title,
                    description=cap.description,
                    properties={
                        "capability_name": cap.name,
                        "status": str(cap.status),
                        "category": str(cap.category),
                        "domain": cap.domain,
                        "owner": cap.owner,
                        "version": cap.version,
                        "supported_operations": [str(op) for op in cap.supported_operations],
                        "search_terms": list(cap.search_terms),
                    },
                    tags=cap.tags,
                )
            )

    # Step 2: Add connected entity nodes and edges
    for cap in capabilities:
        cap_entity_id = f"cap:{cap.name}"

        # 2a. Routes
        for route in cap.routes:
            route_id = f"route:{route}"
            if route_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=route_id,
                        type=PlatformNodeType.ROUTE,
                        name=route,
                        description=f"Frontend route for {cap.title}",
                        properties={"path": route},
                    )
                )
            rel_id = f"rel:{cap.name}-has_route->{route}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.HAS_ROUTE,
                        source_entity_id=cap_entity_id,
                        target_entity_id=route_id,
                    )
                )

        # 2b. APIs
        for api in cap.api_operations:
            api_id = f"api:{api}"
            if api_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=api_id,
                        type=PlatformNodeType.API,
                        name=api,
                        description=f"API operation for {cap.title}",
                        properties={"operation": api},
                    )
                )
            rel_id = f"rel:{cap.name}-exposes_api->{api}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.EXPOSES_API,
                        source_entity_id=cap_entity_id,
                        target_entity_id=api_id,
                    )
                )

        # 2c. Service / Owner
        if cap.owner:
            svc_id = f"service:{cap.owner}"
            if svc_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=svc_id,
                        type=PlatformNodeType.SERVICE,
                        name=cap.owner,
                        description=f"Service component {cap.owner}",
                    )
                )
            rel_id = f"rel:{cap.name}-uses_service->{cap.owner}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.USES_SERVICE,
                        source_entity_id=cap_entity_id,
                        target_entity_id=svc_id,
                    )
                )

        # 2d. Events
        for event_name in cap.events:
            evt_id = f"event:{event_name}"
            if evt_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=evt_id,
                        type=PlatformNodeType.EVENT,
                        name=event_name,
                        description=f"Domain event {event_name}",
                    )
                )
            rel_id = f"rel:{cap.name}-emits_event->{event_name}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.EMITS_EVENT,
                        source_entity_id=cap_entity_id,
                        target_entity_id=evt_id,
                    )
                )

        # 2e. Entities
        for ent_name in cap.entities:
            ent_id = f"entity:{ent_name}"
            if ent_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=ent_id,
                        type=PlatformNodeType.ENTITY,
                        name=ent_name,
                        description=f"Domain entity {ent_name}",
                    )
                )
            rel_id = f"rel:{cap.name}-relates_to_entity->{ent_name}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.RELATES_TO_ENTITY,
                        source_entity_id=cap_entity_id,
                        target_entity_id=ent_id,
                    )
                )

        # 2f. Documentation
        for doc_ref in cap.documentation_references:
            doc_id = f"doc:{doc_ref}"
            if doc_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=doc_id,
                        type=PlatformNodeType.DOCUMENTATION,
                        name=doc_ref,
                        description=f"Documentation reference {doc_ref}",
                    )
                )
            rel_id = f"rel:{cap.name}-has_doc->{doc_ref}"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.HAS_DOCUMENTATION,
                        source_entity_id=cap_entity_id,
                        target_entity_id=doc_id,
                    )
                )

        # 2g. Experience (Assistant & Tour)
        if cap.assistant_description or cap.tour_metadata:
            exp_id = f"experience:{cap.name}"
            if exp_id not in kg._entities:
                await kg.add_entity(
                    Entity(
                        id=exp_id,
                        type=PlatformNodeType.EXPERIENCE,
                        name=f"{cap.title} Experience",
                        description=cap.assistant_description,
                        properties={"tour": cap.tour_metadata},
                    )
                )
            rel_id = f"rel:{cap.name}-has_exp->experience"
            if rel_id not in kg._relationships:
                await kg.add_relationship(
                    Relationship(
                        id=rel_id,
                        type=PlatformEdgeType.HAS_EXPERIENCE,
                        source_entity_id=cap_entity_id,
                        target_entity_id=exp_id,
                    )
                )

        # 2h. Capability Dependencies
        for dep in cap.depends_on:
            dep_cap_id = f"cap:{dep.name}"
            if dep_cap_id in kg._entities:
                rel_id = f"rel:{cap.name}-depends_on->{dep.name}"
                if rel_id not in kg._relationships:
                    await kg.add_relationship(
                        Relationship(
                            id=rel_id,
                            type=PlatformEdgeType.DEPENDS_ON_CAPABILITY,
                            source_entity_id=cap_entity_id,
                            target_entity_id=dep_cap_id,
                        )
                    )

        # 2i. Related Capabilities
        for rel_cap_name in cap.related_capabilities:
            rel_cap_id = f"cap:{rel_cap_name}"
            if rel_cap_id in kg._entities:
                rel_id = f"rel:{cap.name}-related_to->{rel_cap_name}"
                if rel_id not in kg._relationships:
                    await kg.add_relationship(
                        Relationship(
                            id=rel_id,
                            type=PlatformEdgeType.DEPENDS_ON_CAPABILITY,
                            source_entity_id=cap_entity_id,
                            target_entity_id=rel_cap_id,
                        )
                    )

    return kg


class PlatformKnowledgeService:
    """Provides high-level graph queries and permission-scoped topologies."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize service with a built KnowledgeGraph."""
        self._graph = graph
        self._log = get_logger("eaip.kgraph.platform_service")

    async def get_capability_topology(self, capability_name: str) -> dict[str, Any]:
        """Return full topology of nodes connected to the capability.

        Args:
            capability_name: Dot-namespaced capability name (e.g. 'eaip.agents').

        Returns:
            Dictionary containing capability entity and all connected entities by type.
        """
        cap_entity_id = f"cap:{capability_name}"
        if cap_entity_id not in self._graph._entities:
            return {"error": f"Capability {capability_name} not found in graph"}

        cap_entity = await self._graph.get_entity(cap_entity_id)

        # Retrieve outgoing relationships
        out_rels = self._graph._adjacency[cap_entity_id]["out"].values()

        topology: dict[str, Any] = {
            "capability": cap_entity,
            "routes": [],
            "apis": [],
            "services": [],
            "events": [],
            "entities": [],
            "documentation": [],
            "experience": [],
            "dependencies": [],
        }

        for rel in out_rels:
            target = await self._graph.get_entity(rel.target_entity_id)
            if target.type == PlatformNodeType.ROUTE:
                topology["routes"].append(target)
            elif target.type == PlatformNodeType.API:
                topology["apis"].append(target)
            elif target.type == PlatformNodeType.SERVICE:
                topology["services"].append(target)
            elif target.type == PlatformNodeType.EVENT:
                topology["events"].append(target)
            elif target.type == PlatformNodeType.ENTITY:
                topology["entities"].append(target)
            elif target.type == PlatformNodeType.DOCUMENTATION:
                topology["documentation"].append(target)
            elif target.type == PlatformNodeType.EXPERIENCE:
                topology["experience"].append(target)
            elif target.type == PlatformNodeType.CAPABILITY:
                topology["dependencies"].append(target)

        return topology

    async def query_scoped_knowledge(
        self,
        context: PermissionAwareContext,
    ) -> dict[str, Any]:
        """Query platform knowledge scoped to what the given identity CAN SEE.

        Args:
            context: PermissionAwareContext of the authenticated identity.

        Returns:
            Dictionary containing only the capabilities and connected
            entities visible to this identity.
        """
        visible_caps: list[dict[str, Any]] = []

        for cap_name in context.visible_capability_ids:
            topology = await self.get_capability_topology(cap_name)
            if "error" not in topology:
                visible_caps.append(
                    {
                        "capability_name": cap_name,
                        "access": context.get_access(cap_name),
                        "topology": topology,
                    }
                )

        return {
            "identity": context.identity.user_id,
            "tenant_id": context.identity.tenant_id,
            "visible_count": len(visible_caps),
            "capabilities": visible_caps,
        }


__all__ = [
    "PlatformEdgeType",
    "PlatformKnowledgeService",
    "PlatformNodeType",
    "build_platform_knowledge_graph",
]
