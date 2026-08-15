"""Pytest configuration & fixtures for Conductor tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app


@pytest.fixture
async def app():
    """Build and start the EAIP application for testing."""
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()

    c = lifecycle.platform.container
    e = lifecycle.platform.events

    from eaip.agents.registry import AgentRegistry
    from eaip.agents.runtime import AgentRuntime
    from eaip.auth.auth_providers import AuthenticationService
    from eaip.copilot.approvals import ApprovalService
    from eaip.copilot.governance import GovernancePolicy
    from eaip.copilot.memory import GovernedMemoryService
    from eaip.copilot.planner import ConductorPlanner
    from eaip.copilot.service import ConductorService
    from eaip.copilot.tools import build_copilot_tools
    from eaip.runtime.mission import MissionRegistry
    from eaip.workflow.executor import WorkflowEngine
    from eaip.workflow.registry import WorkflowRegistry
    from eaip.memory.engine import MemoryEngine
    from eaip.memory.store import InMemoryStore

    for t, inst in [
        (AgentRegistry, AgentRegistry(event_bus=e)),
        (AgentRuntime, AgentRuntime(llm_adapter=None, tool_registry=None, event_bus=e)),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e)),
        (MemoryEngine, MemoryEngine(InMemoryStore())),
        (WorkflowRegistry, WorkflowRegistry(event_bus=e)),
        (WorkflowEngine, WorkflowEngine(event_bus=e)),
        (MissionRegistry, MissionRegistry(event_bus=e)),
    ]:
        c.register_instance(t, inst)

    # Build Conductor service with its dependencies
    from eaip.tools.registry import ToolRegistry
    from eaip.admin.audit import AuditLogger

    audit_logger = AuditLogger(event_bus=e)
    memory_service = GovernedMemoryService(
        engine=c.resolve(MemoryEngine),
        governance=GovernancePolicy(),
        audit=audit_logger,
    )
    tool_registry = ToolRegistry()
    copilot_tools = build_copilot_tools(
        health_reporter=c.resolve(type(lifecycle.platform.health)),
        agent_registry=c.resolve(AgentRegistry),
        workflow_registry=c.resolve(WorkflowRegistry),
        knowledge_engine=None,
        memory_service=memory_service,
    )
    for tool in copilot_tools.values():
        if tool_registry.try_get(tool.name) is None:
            tool_registry.register(tool)
        else:
            tool_registry.unregister(tool.name)
            tool_registry.register(tool)

    approval_service = ApprovalService(event_bus=e)
    
    conductor_service = ConductorService(
        tool_registry=tool_registry,
        planner=ConductorPlanner(copilot_tools),
        governance=GovernancePolicy(),
        approvals=approval_service,
        audit=audit_logger,
        event_bus=e,
    )
    c.register_instance(ApprovalService, approval_service)
    c.register_instance(AuditLogger, audit_logger)
    c.register_instance(GovernedMemoryService, memory_service)
    c.register_instance(ConductorService, conductor_service)

    fastapi_app = create_app(lifecycle)
    yield fastapi_app, lifecycle
    await lifecycle.stop()


@pytest.fixture
async def client(app):
    """Create an async HTTP client for testing."""
    fastapi_app, _lifecycle = app
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client):
    """Create an authenticated async HTTP client."""
    r = await client.post("/api/auth/login", json={"email": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
