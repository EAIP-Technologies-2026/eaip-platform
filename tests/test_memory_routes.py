from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.http.api import create_app


async def _login(client: AsyncClient, email: str) -> None:
    login = await client.post(
        "/api/auth/login", json={"email": email, "password": "password"}
    )
    client.headers = {"Authorization": f"Bearer {login.json()['token']}"}


@pytest.fixture
async def client():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    lifecycle.platform.container.register_instance(
        AuthenticationService,
        AuthenticationService(secret="test-secret-do-not-use-in-production"),
    )
    app = create_app(lifecycle)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await _login(c, "mem-user")
        yield c
    await lifecycle.stop()


@pytest.mark.asyncio
async def test_memory_create_and_retrieve(client: AsyncClient) -> None:
    """A user can store and retrieve their own memory."""
    item = await client.put(
        "/api/memory/mem-test-001",
        json={"value": "Test memory content", "tags": ["test"]},
    )
    assert item.status_code == 200
    assert item.json()["id"] == "mem-test-001"
    assert item.json()["value"] == "Test memory content"

    retrieved = await client.get("/api/memory/mem-test-001")
    assert retrieved.status_code == 200
    assert retrieved.json()["value"] == "Test memory content"


@pytest.mark.asyncio
async def test_memory_search(client: AsyncClient) -> None:
    """User can search their memories by content."""
    await client.put(
        "/api/memory/mem-search-001",
        json={"value": "Machine learning model training data"},
    )

    results = await client.get("/api/memory/search?q=machine+learning")
    assert results.status_code == 200


@pytest.mark.asyncio
async def test_memory_tenant_isolation(
    client: AsyncClient,
) -> None:
    """A second user (different tenant) cannot see the first user's memory."""
    # Tenant A creates a memory
    created = await client.put(
        "/api/memory/isolated-mem-001",
        json={"value": "Secret tenant A data"},
    )
    assert created.status_code == 200

    # Tenant A can retrieve it
    own = await client.get("/api/memory/isolated-mem-001")
    assert own.status_code == 200
    assert own.json()["value"] == "Secret tenant A data"

    # Switch to tenant B
    old_headers = dict(client.headers)
    await _login(client, "another-user")

    # Tenant B should NOT see tenant A's memory
    attempt = await client.get("/api/memory/isolated-mem-001")
    assert attempt.status_code == 404

    # Restore
    client.headers = old_headers
