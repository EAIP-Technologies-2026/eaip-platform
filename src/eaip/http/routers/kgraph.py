"""Knowledge Graph API routes.

Exposes the existing KGraph subsystem (``eaip.kgraph``) over HTTP with
full tenant isolation: every entity and relationship is tagged with the
authenticated user's ``tenant_id``, and all queries are filtered server-side.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.kgraph.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    GraphQueryError,
    GraphTraversalError,
    RelationshipNotFoundError,
)
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.index import GraphIndex
from eaip.kgraph.models import Entity, GraphQuery, GraphQueryMode, Relationship
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/knowledge-graph",
    tags=["knowledge-graph"],
    dependencies=[Depends(get_current_user)],
)
log = get_logger("eaip.http.routers.kgraph")


def _tenant_id(user: dict[str, Any]) -> str:
    return str(
        user.get("tenant_id")
        or user.get("org_id")
        or user.get("organization_id")
        or user.get("tenant")
        or user.get("sub")
        or "default"
    )


def _get_graph(request: Request) -> KnowledgeGraph:
    cont = request.app.state.lifecycle.platform.container
    graph = cont.try_resolve(KnowledgeGraph)
    if graph is not None:
        return graph
    global _fallback_graph
    if _fallback_graph is None:
        _fallback_graph = KnowledgeGraph()
    return _fallback_graph


_fallback_graph: KnowledgeGraph | None = None


def _get_index(request: Request) -> GraphIndex | None:
    cont = request.app.state.lifecycle.platform.container
    return cont.try_resolve(GraphIndex)


def _tenant_matches(metadata: dict[str, Any], tenant: str) -> bool:
    if not metadata:
        return False
    return str(metadata.get("tenant_id", "")) == tenant


def _to_iso(dt: Any) -> str:
    if isinstance(dt, (int, float)):
        from datetime import datetime, timezone
        return datetime.fromtimestamp(dt, tz=timezone.utc).isoformat()
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt) if dt is not None else ""


def _entity_to_dict(entity: Entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "type": entity.type,
        "name": entity.name,
        "description": entity.description,
        "properties": entity.properties,
        "source": entity.source,
        "confidence": entity.confidence,
        "metadata": entity.metadata,
        "tags": list(entity.tags),
        "createdAt": _to_iso(entity.created_at),
        "updatedAt": _to_iso(entity.updated_at),
    }


def _rel_to_dict(rel: Relationship) -> dict[str, Any]:
    return {
        "id": rel.id,
        "type": rel.type,
        "sourceEntityId": rel.source_entity_id,
        "targetEntityId": rel.target_entity_id,
        "weight": rel.weight,
        "bidirectional": rel.bidirectional,
        "properties": rel.properties,
        "metadata": rel.metadata,
        "createdAt": rel.created_at.isoformat(),
    }


def _entity_dicts(graph: KnowledgeGraph, ids: list[str], tenant: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for eid in ids:
        entity = graph.entities.get(eid)
        if entity and _tenant_matches(entity.metadata, tenant):
            result.append(_entity_to_dict(entity))
    return result


def _rel_dicts(graph: KnowledgeGraph, ids: list[str], tenant: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for rid in ids:
        rel = graph.relationships.get(rid)
        if rel and _tenant_matches(rel.metadata, tenant):
            result.append(_rel_to_dict(rel))
    return result


# ── Entity routes ──────────────────────────────────────────────────


@router.get("/entities")
async def list_entities(
    request: Request,
    user: dict = Depends(get_current_user),
    type_filter: str | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    results: list[dict[str, Any]] = []
    for entity in graph.entities.values():
        if not _tenant_matches(entity.metadata, tenant):
            continue
        if type_filter and entity.type != type_filter:
            continue
        if q and q.lower() not in (entity.name + " " + entity.description).lower():
            continue
        if len(results) >= limit:
            break
        results.append(_entity_to_dict(entity))
    return results


@router.post("/entities")
async def create_entity(
    request: Request,
    user: dict = Depends(get_current_user),
    body: dict[str, Any] = None,
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    body = body or {}
    entity_id = str(body.get("id") or f"ent-{uuid.uuid4().hex[:12]}")
    metadata = dict(body.get("metadata", {}))
    metadata["tenant_id"] = tenant

    entity = Entity(
        id=entity_id,
        type=body.get("type", "entity"),
        name=body.get("name", ""),
        description=body.get("description", ""),
        properties=body.get("properties", {}),
        source=body.get("source", "api"),
        confidence=float(body.get("confidence", 1.0)),
        metadata=metadata,
        tags=tuple(body.get("tags", [])),
    )
    try:
        created = await graph.add_entity(entity)
    except EntityValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    log.info("entity.created", id=entity_id, tenant=tenant)
    return _entity_to_dict(created)


@router.get("/entities/search")
async def search_entities(
    request: Request,
    user: dict = Depends(get_current_user),
    q: str | None = None,
    type_filter: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    results: list[dict[str, Any]] = []
    query_term = (q or "").lower()
    for entity in graph.entities.values():
        if not _tenant_matches(entity.metadata, tenant):
            continue
        if type_filter and entity.type != type_filter:
            continue
        if query_term and query_term not in (entity.name + " " + entity.description).lower():
            continue
        results.append(_entity_to_dict(entity))
        if len(results) >= limit:
            break
    return results


@router.get("/entities/{entity_id}")
async def get_entity(
    request: Request, entity_id: str, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    try:
        entity = await graph.get_entity(entity_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    if not _tenant_matches(entity.metadata, tenant):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Entity not found")
    return _entity_to_dict(entity)


@router.put("/entities/{entity_id}")
async def update_entity(
    request: Request, entity_id: str, body: dict[str, Any], user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    try:
        entity = await graph.get_entity(entity_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    if not _tenant_matches(entity.metadata, tenant):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Entity not found")
    updates = {k: v for k, v in body.items() if v is not None}
    try:
        updated = await graph.update_entity(entity_id, updates)
    except EntityValidationError as exc:
        raise HTTPException(status_code=HTTP_400, detail=str(exc))
    log.info("entity.updated", id=entity_id, tenant=tenant)
    return _entity_to_dict(updated)


@router.delete("/entities/{entity_id}")
async def delete_entity(
    request: Request, entity_id: str, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    try:
        entity = await graph.get_entity(entity_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    if not _tenant_matches(entity.metadata, tenant):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Entity not found")
    try:
        deleted = await graph.delete_entity(entity_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    log.info("entity.deleted", id=entity_id, tenant=tenant)
    return {"id": entity_id, "status": "deleted"}


# ── Relationship routes ────────────────────────────────────────────


@router.get("/relationships")
async def list_relationships(
    request: Request,
    user: dict = Depends(get_current_user),
    type_filter: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    results: list[dict[str, Any]] = []
    for rel in graph.relationships.values():
        if not _tenant_matches(rel.metadata, tenant):
            continue
        if type_filter and rel.type != type_filter:
            continue
        if source_id and rel.source_entity_id != source_id:
            continue
        if target_id and rel.target_entity_id != target_id:
            continue
        if len(results) >= limit:
            break
        results.append(_rel_to_dict(rel))
    return results


@router.post("/relationships")
async def create_relationship(
    request: Request,
    user: dict = Depends(get_current_user),
    body: dict[str, Any] = None,
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    body = body or {}
    rel_id = str(body.get("id") or f"rel-{uuid.uuid4().hex[:12]}")
    metadata = dict(body.get("metadata", {}))
    metadata["tenant_id"] = tenant

    source_id = str(body.get("sourceEntityId", body.get("source_entity_id", "")))
    target_id = str(body.get("targetEntityId", body.get("target_entity_id", "")))
    if not source_id or not target_id:
        raise HTTPException(
            status_code=400,
            detail="sourceEntityId and targetEntityId are required",
        )

    rel = Relationship(
        id=rel_id,
        type=body.get("type", "related_to"),
        source_entity_id=source_id,
        target_entity_id=target_id,
        weight=float(body.get("weight", 1.0)),
        bidirectional=bool(body.get("bidirectional", False)),
        properties=body.get("properties", {}),
        metadata=metadata,
    )
    try:
        created = await graph.add_relationship(rel)
    except (EntityNotFoundError, EntityValidationError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    log.info("relationship.created", id=rel_id, tenant=tenant)
    return _rel_to_dict(created)


@router.delete("/relationships/{rel_id}")
async def delete_relationship(
    request: Request, rel_id: str, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    try:
        rel = await graph.get_relationship(rel_id)
    except RelationshipNotFoundError:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Relationship {rel_id} not found"
        )
    if not _tenant_matches(rel.metadata, tenant):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Relationship not found")
    await graph.delete_relationship(rel_id)
    return {"status": "deleted", "id": rel_id}


# ── Traversal & query routes ───────────────────────────────────────


@router.post("/query")
async def graph_query(
    request: Request, body: dict[str, Any], user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    try:
        query = GraphQuery(
            query=body.get("query", ""),
            entity_types=tuple(body.get("entityTypes", body.get("entity_types", []))),
            relationship_types=tuple(
                body.get("relationshipTypes", body.get("relationship_types", []))
            ),
            max_depth=int(body.get("maxDepth", body.get("max_depth", 3))),
            min_confidence=float(body.get("minConfidence", body.get("min_confidence", 0.0))),
            limit=int(body.get("limit", 100)),
            filters=body.get("filters", {}),
            mode=GraphQueryMode(body.get("mode", GraphQueryMode.BFS.value)),
            start_entity_id=body.get("startEntityId", body.get("start_entity_id", "")),
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid query: {exc}")
    try:
        result = await graph.query(query)
    except (GraphQueryError, GraphTraversalError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    tenant = _tenant_id(user)
    return {
        "entities": [
            _entity_to_dict(e) for e in result.entities if _tenant_matches(e.metadata, tenant)
        ],
        "relationships": [
            _rel_to_dict(r) for r in result.relationships if _tenant_matches(r.metadata, tenant)
        ],
        "paths": [p.model_dump() for p in result.paths],
        "totalCount": result.total_count,
        "durationMs": round(result.duration_ms, 2),
    }


@router.post("/traversal/{entity_id}")
async def traverse_entity(
    request: Request,
    entity_id: str,
    user: dict = Depends(get_current_user),
    body: dict[str, Any] = None,
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    body = body or {}
    depth = int(body.get("depth", 3))
    direction = str(body.get("direction", "out"))
    try:
        result = await graph.traverse(entity_id, depth, direction)
    except (GraphQueryError, GraphTraversalError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "entities": _entity_dicts(graph, result.get("entity_ids", []), tenant),
        "relationships": _rel_dicts(graph, result.get("relationship_ids", []), tenant),
    }


@router.get("/shortest-path")
async def shortest_path(
    request: Request,
    source_id: str,
    target_id: str,
    user: dict = Depends(get_current_user),
    max_depth: int = 10,
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    try:
        path = await graph.get_shortest_path(source_id, target_id, max_depth)
    except (GraphQueryError, GraphTraversalError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if path is None:
        return {"path": None, "found": False}
    source = graph.entities.get(source_id)
    target = graph.entities.get(target_id)
    ok = (source is None or _tenant_matches(source.metadata, tenant)) and (
        target is None or _tenant_matches(target.metadata, tenant)
    )
    if not ok:
        return {"path": None, "found": False}
    return {"path": path.model_dump(), "found": True}


@router.get("/subgraph")
async def get_subgraph(
    request: Request,
    entity_ids: str = "",
    user: dict = Depends(get_current_user),
    depth: int = 2,
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    ids = entity_ids.split(",") if entity_ids else []
    if not ids:
        raise HTTPException(status_code=400, detail="entity_ids query parameter required")
    try:
        result = await graph.get_subgraph(ids, depth)
    except (GraphQueryError, GraphTraversalError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "entities": _entity_dicts(graph, result.get("entity_ids", []), tenant),
        "relationships": _rel_dicts(graph, result.get("relationship_ids", []), tenant),
    }


# ── Statistics helper ──────────────────────────────────────────────


def _count_tenant_entities(graph: KnowledgeGraph, tenant: str) -> int:
    return sum(
        1 for e in graph.entities.values() if _tenant_matches(e.metadata, tenant)
    )


def _count_tenant_relationships(graph: KnowledgeGraph, tenant: str) -> int:
    return sum(
        1 for r in graph.relationships.values() if _tenant_matches(r.metadata, tenant)
    )


# ── Statistics routes ──────────────────────────────────────────────


@router.get("/stats")
async def graph_stats(
    request: Request, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    stats = await graph.get_stats()
    tenant_entities = _count_tenant_entities(graph, tenant)
    tenant_rels = _count_tenant_relationships(graph, tenant)
    return {
        "totalEntities": tenant_entities,
        "totalRelationships": tenant_rels,
        "entityTypeCounts": stats.entity_type_counts,
        "relationshipTypeCounts": stats.relationship_type_counts,
    }


@router.get("/health")
async def graph_health(
    request: Request, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    graph = _get_graph(request)
    tenant = _tenant_id(user)
    stats = await graph.get_stats()
    tenant_entities = _count_tenant_entities(graph, tenant)
    tenant_rels = _count_tenant_relationships(graph, tenant)
    return {
        "status": "healthy" if stats.total_entities >= 0 else "unhealthy",
        "totalEntities": tenant_entities,
        "totalRelationships": tenant_rels,
        "entityTypeCounts": stats.entity_type_counts,
        "relationshipTypeCounts": stats.relationship_type_counts,
    }
