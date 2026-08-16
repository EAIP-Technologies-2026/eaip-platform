from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.http.api import create_app


async def _login(client: AsyncClient, email: str) -> AsyncClient:
    login = await client.post("/api/auth/login", json={"email": email, "password": "password"})
    client.headers = {"Authorization": f"Bearer {login.json()['token']}"}
    return client


@pytest.fixture
async def tenant_client():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    lifecycle.platform.container.register_instance(
        AuthenticationService,
        AuthenticationService(secret="test-secret-do-not-use-in-production"),
    )
    app = create_app(lifecycle)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, "kg-user")
        yield client
    await lifecycle.stop()


@pytest.mark.asyncio
async def test_entity_crud(tenant_client: AsyncClient) -> None:
    # Create entity
    created = await tenant_client.post(
        "/api/knowledge-graph/entities",
        json={
            "id": "test-entity-1",
            "type": "concept",
            "name": "Test Concept",
            "description": "A test concept for testing",
            "properties": {"category": "test"},
        },
    )
    assert created.status_code == 200
    entity = created.json()
    assert entity["id"] == "test-entity-1"
    assert entity["name"] == "Test Concept"
    assert entity["type"] == "concept"

    # Get entity
    retrieved = await tenant_client.get("/api/knowledge-graph/entities/test-entity-1")
    assert retrieved.status_code == 200
    assert retrieved.json()["name"] == "Test Concept"

    # Update entity
    updated = await tenant_client.put(
        "/api/knowledge-graph/entities/test-entity-1",
        json={"name": "Updated Concept"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Concept"

    # List entities
    listed = await tenant_client.get("/api/knowledge-graph/entities")
    assert listed.status_code == 200
    assert any(e["id"] == "test-entity-1" for e in listed.json())

    # Delete entity
    deleted = await tenant_client.delete("/api/knowledge-graph/entities/test-entity-1")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    # Verify deletion
    retrieval = await tenant_client.get("/api/knowledge-graph/entities/test-entity-1")
    assert retrieval.status_code == 404


@pytest.mark.asyncio
async def test_graph_stats(tenant_client: AsyncClient) -> None:
    # Create an entity first
    await tenant_client.post(
        "/api/knowledge-graph/entities",
        json={"id": "stats-entity-1", "type": "concept", "name": "Stats Entity"},
    )

    stats = await tenant_client.get("/api/knowledge-graph/stats")
    assert stats.status_code == 200
    data = stats.json()
    assert "totalEntities" in data
    assert data["totalEntities"] >= 1
    assert "entityTypeCounts" in data


@pytest.mark.asyncio
async def test_tenant_isolation_entity(tenant_client: AsyncClient) -> None:
    # Switch to tenant B's auth token
    old_headers = dict(tenant_client.headers)

    # Tenant A creates an entity
    created = await tenant_client.post(
        "/api/knowledge-graph/entities",
        json={"id": "shared-entity", "type": "concept", "name": "Shared Entity"},
    )
    assert created.status_code == 200

    # Switch to tenant B
    await _login(tenant_client, "another-owner")

    # Tenant B should NOT see the entity
    attempt = await tenant_client.get("/api/knowledge-graph/entities/shared-entity")
    assert attempt.status_code == 404

    # Tenant B should NOT see it in the list
    listed = await tenant_client.get("/api/knowledge-graph/entities")
    assert listed.status_code == 200
    assert not any(e["id"] == "shared-entity" for e in listed.json())

    # Tenant B should NOT be able to update/delete it
    update_attempt = await tenant_client.put(
        "/api/knowledge-graph/entities/shared-entity",
        json={"name": "Hacked"},
    )
    assert update_attempt.status_code == 404

    delete_attempt = await tenant_client.delete(
        "/api/knowledge-graph/entities/shared-entity"
    )
    assert delete_attempt.status_code == 404

    # Restore original auth
    tenant_client.headers = old_headers


@pytest.mark.asyncio
async def test_relationship_crud(tenant_client: AsyncClient) -> None:
    # Create source and target entities
    await tenant_client.post(
        "/api/knowledge-graph/entities",
        json={"id": "rel-src", "type": "concept", "name": "Source"},
    )
    await tenant_client.post(
        "/api/knowledge-graph/entities",
        json={"id": "rel-tgt", "type": "concept", "name": "Target"},
    )

    # Create relationship
    created = await tenant_client.post(
        "/api/knowledge-graph/relationships",
        json={
            "id": "rel-1",
            "type": "related_to",
            "sourceEntityId": "rel-src",
            "targetEntityId": "rel-tgt",
            "weight": 0.8,
        },
    )
    assert created.status_code == 200
    rel = created.json()
    assert rel["id"] == "rel-1"
    assert rel["sourceEntityId"] == "rel-src"
    assert rel["targetEntityId"] == "rel-tgt"

    # List relationships
    listed = await tenant_client.get("/api/knowledge-graph/relationships")
    assert listed.status_code == 200
    assert any(r["id"] == "rel-1" for r in listed.json())

    # Delete relationship
    deleted = await tenant_client.delete("/api/knowledge-graph/relationships/rel-1")
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_graph_traversal(tenant_client: AsyncClient) -> None:
    # Create entities and relationships
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "t-a", "type": "concept", "name": "A"})
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "t-b", "type": "concept", "name": "B"})
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "t-c", "type": "concept", "name": "C"})

    await tenant_client.post("/api/knowledge-graph/relationships", json={
        "id": "t-rel-ab", "type": "links_to", "sourceEntityId": "t-a", "targetEntityId": "t-b",
    })
    await tenant_client.post("/api/knowledge-graph/relationships", json={
        "id": "t-rel-bc", "type": "links_to", "sourceEntityId": "t-b", "targetEntityId": "t-c",
    })

    # Traverse from A
    traversal = await tenant_client.post(
        "/api/knowledge-graph/traversal/t-a",
        json={"depth": 2, "direction": "out"},
    )
    assert traversal.status_code == 200
    data = traversal.json()
    entity_ids = {e["id"] for e in data["entities"]}
    assert "t-a" in entity_ids
    assert "t-b" in entity_ids


@pytest.mark.asyncio
async def test_graph_query(tenant_client: AsyncClient) -> None:
    await tenant_client.post("/api/knowledge-graph/entities", json={
        "id": "q-src", "type": "concept", "name": "QuerySource",
    })

    resp = await tenant_client.post(
        "/api/knowledge-graph/query",
        json={"query": "QuerySource", "mode": "bfs", "startEntityId": "q-src", "maxDepth": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "entities" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_graph_shortest_path(tenant_client: AsyncClient) -> None:
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "p-a", "type": "concept", "name": "A"})
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "p-b", "type": "concept", "name": "B"})
    await tenant_client.post("/api/knowledge-graph/entities", json={"id": "p-c", "type": "concept", "name": "C"})

    await tenant_client.post("/api/knowledge-graph/relationships", json={
        "id": "p-rel-1", "type": "linked", "sourceEntityId": "p-a", "targetEntityId": "p-b",
    })
    await tenant_client.post("/api/knowledge-graph/relationships", json={
        "id": "p-rel-2", "type": "linked", "sourceEntityId": "p-b", "targetEntityId": "p-c",
    })

    path_resp = await tenant_client.get(
        "/api/knowledge-graph/shortest-path",
        params={"source_id": "p-a", "target_id": "p-c"},
    )
    assert path_resp.status_code == 200
    data = path_resp.json()
    assert data["found"] is True
    assert data["path"] is not None


@pytest.mark.asyncio
async def test_graph_entity_search(tenant_client: AsyncClient) -> None:
    await tenant_client.post("/api/knowledge-graph/entities", json={
        "id": "search-entity-1", "type": "document", "name": "Financial Report 2024",
    })

    search_resp = await tenant_client.get(
        "/api/knowledge-graph/entities/search",
        params={"q": "Financial"},
    )
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert any(e["name"] == "Financial Report 2024" for e in results)


@pytest.mark.asyncio
async def test_graph_health(tenant_client: AsyncClient) -> None:
    health = await tenant_client.get("/api/knowledge-graph/health")
    assert health.status_code == 200
    data = health.json()
    assert "status" in data
