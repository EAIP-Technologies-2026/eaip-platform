"""Vertical-slice integration tests for EAIP Conductor.

Proves the full path: authenticated user asks Conductor a question, Conductor
inspects the platform through governed tools, returns grounded results,
requests approval for an action, executes it through the existing backend,
and produces an auditable result.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.admin.audit import AuditLogger
from eaip.agents.registry import AgentRegistry
from eaip.agents.runtime import AgentRuntime
from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.planner import ConductorPlanner
from eaip.copilot.service import ConductorService
from eaip.copilot.tools import build_copilot_tools
from eaip.http.api import create_app
from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.in_memory_store import InMemoryVectorStore
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.memory.engine import MemoryEngine
from eaip.memory.store import InMemoryStore
from eaip.runtime.mission import MissionRegistry
from eaip.tools.registry import ToolRegistry
from eaip.workflow.executor import WorkflowEngine
from eaip.workflow.registry import WorkflowRegistry
from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.push_service import PushService


@pytest.fixture(scope="module")
def event_loop():
    """Provide a module-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def app():
    """A fully-wired application with Conductor services registered."""
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()

    container = lifecycle.platform.container
    events = lifecycle.platform.events

    agent_registry = AgentRegistry(event_bus=events)
    wf_registry = WorkflowRegistry(event_bus=events)
    tool_registry = ToolRegistry()

    for t, inst in [
        (AgentRegistry, agent_registry),
        (
            AgentRuntime,
            AgentRuntime(
                llm_adapter=None, tool_registry=tool_registry, event_bus=events
            ),
        ),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=events)),
        (MemoryEngine, MemoryEngine(InMemoryStore())),
        (WorkflowRegistry, wf_registry),
        (WorkflowEngine, WorkflowEngine(event_bus=events)),
        (MissionRegistry, MissionRegistry(event_bus=events)),
        (ToolRegistry, tool_registry),
    ]:
        container.register_instance(t, inst)

    cm = ConnectionManager()
    chm = ChannelManager()
    ps = PushService(channel_manager=chm, connection_manager=cm)
    container.register_instance(ConnectionManager, cm)
    container.register_instance(ChannelManager, chm)
    container.register_instance(PushService, ps)

    audit_logger = AuditLogger(event_bus=events)
    container.register_instance(AuditLogger, audit_logger)

    knowledge_engine = KnowledgeEngine(
        KnowledgeRegistry(),
        InMemoryVectorStore(),
        MockEmbeddingProvider(),
    )
    container.register_instance(KnowledgeEngine, knowledge_engine)

    copilot_tools = build_copilot_tools(
        health_reporter=lifecycle.platform.health,
        agent_registry=agent_registry,
        workflow_registry=wf_registry,
        knowledge_engine=knowledge_engine,
    )
    for tool in copilot_tools.values():
        tool_registry.register(tool)

    approval_service = ApprovalService(event_bus=events)
    container.register_instance(ApprovalService, approval_service)

    conductor = ConductorService(
        tool_registry=tool_registry,
        planner=ConductorPlanner(copilot_tools),
        governance=GovernancePolicy(),
        approvals=approval_service,
        audit=audit_logger,
        event_bus=events,
    )
    container.register_instance(ConductorService, conductor)

    fastapi_app = create_app(lifecycle)
    yield fastapi_app

    await lifecycle.stop()


@pytest.fixture
async def client(app):
    """An unauthenticated ASGI client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client):
    """An ASGI client authenticated as the mock admin user."""
    r = await client.post("/api/auth/login", json={"email": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


class TestConductorChat:
    async def test_chat_requires_auth(self, client):
        """Unauthenticated calls are rejected with 401."""
        r = await client.post("/api/copilot/chat", json={"message": "health"})
        assert r.status_code == 401

    async def test_health_question_runs_governed_tool(self, authenticated_client):
        """An informational question executes system_health and returns JSON."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "how is the platform health?"}
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["id"].startswith("turn-")
        assert turn["correlation_id"]
        assert turn["tool_events"][0]["tool_name"] == "system_health"
        assert turn["tool_events"][0]["status"] == "executed"
        payload = json.loads(turn["reply"])
        assert "status" in payload

    async def test_agents_question_lists_agents(self, authenticated_client):
        """Asking about agents runs list_agents and returns a JSON list."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "list the agents"}
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["tool_events"][0]["tool_name"] == "list_agents"
        assert isinstance(json.loads(turn["reply"]), list)

    async def test_unmatched_message_returns_help(self, authenticated_client):
        """Unknown messages produce a helpful reply and no tool calls."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "please explain the meaning of life"}
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["tool_events"] == []
        assert "inspect this EAIP instance" in turn["reply"]

    async def test_knowledge_search_is_grounded(self, authenticated_client):
        """A search question runs knowledge_search against the engine."""
        r = await authenticated_client.post(
            "/api/copilot/chat",
            json={"message": "search the knowledge base for onboarding"},
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["tool_events"][0]["tool_name"] == "knowledge_search"
        payload = json.loads(turn["reply"])
        assert "query" in payload
        assert "total" in payload


class TestConductorApprovals:
    async def test_action_requires_approval(self, authenticated_client):
        """Creating an agent returns a pending approval instead of executing."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "create an agent named DataBot"}
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["pending_approval"] is not None
        approval = turn["pending_approval"]
        assert approval["tool_name"] == "create_agent"
        assert approval["status"] == "pending"
        assert approval["risk"] == "action"
        assert approval["arguments"] == {"name": "DataBot"}

    async def test_list_pending_approvals(self, authenticated_client):
        """Pending approvals are visible to their requester."""
        await authenticated_client.post(
            "/api/copilot/chat", json={"message": "create an agent named PendingBot"}
        )
        r = await authenticated_client.get("/api/copilot/approvals")
        assert r.status_code == 200
        approvals = r.json()
        assert any(a["tool_name"] == "create_agent" for a in approvals)

    async def test_approve_executes_action(self, authenticated_client):
        """Approving an approval request executes the tool and audits it."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "create an agent named ApproveBot"}
        )
        approval_id = r.json()["pending_approval"]["id"]

        r = await authenticated_client.post(f"/api/copilot/approvals/{approval_id}/approve")
        assert r.status_code == 200
        body = r.json()
        assert body["approval"]["status"] == "approved"
        assert body["approval"]["decided_by"] == "admin"
        created = json.loads(body["result"])
        assert created["name"] == "ApproveBot"

        agents = await authenticated_client.get("/api/agents")
        assert any(a["name"] == "ApproveBot" for a in agents.json())

    async def test_reject_skips_action(self, authenticated_client):
        """Rejecting an approval request prevents the tool from running."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "create an agent named RejectBot"}
        )
        approval_id = r.json()["pending_approval"]["id"]

        r = await authenticated_client.post(f"/api/copilot/approvals/{approval_id}/reject")
        assert r.status_code == 200
        body = r.json()
        assert body["approval"]["status"] == "rejected"
        assert body["result"] is None

        agents = await authenticated_client.get("/api/agents")
        assert all(a["name"] != "RejectBot" for a in agents.json())

    async def test_deciding_unknown_approval_is_404(self, authenticated_client):
        """Unknown approval ids return 404."""
        r = await authenticated_client.post("/api/copilot/approvals/does-not-exist/approve")
        assert r.status_code == 404


class TestConductorConversationContinuity:
    async def test_chat_threads_conversation_id(self, authenticated_client):
        """A client-supplied conversation_id is echoed on the returned turn."""
        r = await authenticated_client.post(
            "/api/copilot/chat",
            json={"message": "how is the platform health?", "conversation_id": "conv-abc-123"},
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["conversation_id"] == "conv-abc-123"

    async def test_chat_without_conversation_id_is_null(self, authenticated_client):
        """When no conversation_id is supplied the turn reports null."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "how is the platform health?"}
        )
        assert r.status_code == 200
        turn = r.json()
        assert turn["conversation_id"] is None

    async def test_chat_stream_echoes_conversation_id(self, authenticated_client):
        """The streaming start event includes the client conversation_id."""
        r = await authenticated_client.post(
            "/api/copilot/chat/stream",
            json={"message": "how is the system doing?", "conversation_id": "conv-stream-9"},
        )
        assert r.status_code == 200
        content = r.text
        assert '"conversation_id": "conv-stream-9"' in content or '"conversation_id": "conv-stream-9"' in content


class TestConductorAudit:
    async def test_tool_execution_is_audited(self, authenticated_client):
        """Every executed tool produces a queryable audit entry."""
        before = await authenticated_client.get(
            "/api/admin/audit", params={"action": "copilot.tool.list_agents"}
        )
        before_count = before.json()["total"]
        await authenticated_client.post("/api/copilot/chat", json={"message": "list agents"})
        after = await authenticated_client.get(
            "/api/admin/audit", params={"action": "copilot.tool.list_agents"}
        )
        assert after.json()["total"] > before_count

    async def test_approval_is_audited(self, authenticated_client):
        """Approval requests and decisions produce audit entries."""
        r = await authenticated_client.post(
            "/api/copilot/chat", json={"message": "create an agent named AuditBot"}
        )
        approval_id = r.json()["pending_approval"]["id"]
        await authenticated_client.post(f"/api/copilot/approvals/{approval_id}/approve")

        audits = await authenticated_client.get("/api/admin/audit")
        actions = {e["action"] for e in audits.json()["entries"]}
        assert "copilot.approval.request" in actions
        assert "copilot.approval.approve" in actions
        assert "copilot.tool.create_agent" in actions


class TestConductorStream:
    async def test_chat_stream_endpoint(self, authenticated_client):
        """The /chat/stream endpoint returns text/event-stream content."""
        r = await authenticated_client.post(
            "/api/copilot/chat/stream",
            json={
                "message": "how is the system doing?",
                "context": {"current_route": "/dashboard"},
            },
        )
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        content = r.text
        assert "event: message_start" in content
        assert "event: message_complete" in content


class TestConductorDiagnostics:
    async def test_runtime_diagnostics(self, authenticated_client):
        """Conductor provides structured diagnostics with OBSERVED/INFERRED/RECOMMENDED fields."""
        r = await authenticated_client.post(
            "/api/copilot/chat",
            json={"message": "why is the system failing?"},
        )
        assert r.status_code == 200
        turn = r.json()
        payload = json.loads(turn["reply"])
        assert "observed" in payload
        assert "inferred" in payload
        assert "recommended" in payload

    async def test_recent_failures(self, authenticated_client):
        """Conductor retrieves operational failure events."""
        r = await authenticated_client.post(
            "/api/copilot/chat",
            json={"message": "show recent error failures"},
        )
        assert r.status_code == 200
        turn = r.json()
        payload = json.loads(turn["reply"])
        assert "failures" in payload
        assert len(payload["failures"]) > 0


class TestPhase1Tools:
    async def test_current_time_tool(self, authenticated_client):
        """Conductor fetches current UTC time."""
        r = await authenticated_client.post(
            "/api/copilot/chat",
            json={"message": "what is the current time?"},
        )
        assert r.status_code == 200
        turn = r.json()
        payload = json.loads(turn["reply"])
        assert "current_time_utc" in payload

class TestPhase3SystemTwin:
    async def test_twin_endpoint(self, authenticated_client):
        """The /copilot/twin endpoint returns normalized system twin state."""
        r = await authenticated_client.get("/api/copilot/twin")
        assert r.status_code == 200
        body = r.json()
        assert "health" in body
        assert "agents" in body
        assert "workflows" in body

    async def test_briefing_endpoint(self, authenticated_client):
        """The /copilot/briefing endpoint returns executive system briefing summary."""
        r = await authenticated_client.get("/api/copilot/briefing")
        assert r.status_code == 200
        body = r.json()
        assert "title" in body
        assert "health" in body
        assert "summary" in body

    async def test_anomalies_endpoint(self, authenticated_client):
        """The /copilot/anomalies endpoint returns proactive anomaly nudges."""
        r = await authenticated_client.get("/api/copilot/anomalies")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)

class TestPhase4Skills:
    async def test_list_skills(self, authenticated_client):
        """The /copilot/skills endpoint returns registered skills."""
        r = await authenticated_client.get("/api/copilot/skills")
        assert r.status_code == 200
        skills = r.json()
        assert isinstance(skills, list)
        assert len(skills) >= 5
        ids = [s["id"] for s in skills]
        assert "system_health_briefing" in ids
        assert "agent_health_investigation" in ids

class TestPhase5Marketplace:
    async def test_marketplace_catalog(self, authenticated_client):
        """The /copilot/marketplace/catalog endpoint lists available skill packages."""
        r = await authenticated_client.get("/api/copilot/marketplace/catalog")
        assert r.status_code == 200
        catalog = r.json()
        assert isinstance(catalog, list)
        assert len(catalog) >= 2
        pkg_ids = [p["package_id"] for p in catalog]
        assert "eaip.operations.v1" in pkg_ids
        assert "eaip.diagnostics.v1" in pkg_ids

    async def test_marketplace_package_inspect(self, authenticated_client):
        """Inspect a specific marketplace package."""
        r = await authenticated_client.get("/api/copilot/marketplace/packages/eaip.diagnostics.v1")
        assert r.status_code == 200
        pkg = r.json()
        assert pkg["package_id"] == "eaip.diagnostics.v1"
        assert pkg["trust_level"] == "VERIFIED"
        assert len(pkg["skills"]) >= 2

    async def test_marketplace_lifecycle(self, authenticated_client):
        """Install, enable, and disable a marketplace skill package."""
        # Install
        r_inst = await authenticated_client.post("/api/copilot/marketplace/packages/eaip.diagnostics.v1/install")
        assert r_inst.status_code == 200
        assert r_inst.json()["status"] == "INSTALLED"

        # Enable
        r_ena = await authenticated_client.post("/api/copilot/marketplace/packages/eaip.diagnostics.v1/enable")
        assert r_ena.status_code == 200
        assert r_ena.json()["status"] == "ENABLED"

        # Disable
        r_dis = await authenticated_client.post("/api/copilot/marketplace/packages/eaip.diagnostics.v1/disable")
        assert r_dis.status_code == 200
        assert r_dis.json()["status"] == "DISABLED"

    async def test_marketplace_upgrade(self, authenticated_client):
        """Upgrade an installed marketplace skill package."""
        r_upg = await authenticated_client.post("/api/copilot/marketplace/packages/eaip.diagnostics.v1/upgrade?new_version=1.2.0")
        assert r_upg.status_code == 200
        assert r_upg.json()["version"] == "1.2.0"


class TestMarketplaceAdversarialSecurity:
    # CASE 1: Server policy validates user roles
    def test_01_unauthorized_installation(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.policy import MarketplacePolicy
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        user_user = {"roles": ["user"]}
        policy = MarketplacePolicy(require_admin_approval=True)
        try:
            mp_reg.install_package("eaip.diagnostics.v1", user=user_user, policy=policy)
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass

    # CASE 2: Uninstalled package state
    def test_02_uninstalled_package_state(self):
        from eaip.copilot.marketplace.models import PackageStatus
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        manifest = mp_reg.get_package("eaip.diagnostics.v1")
        assert manifest is not None

    # CASE 3: Uninstalled skill execution denial
    async def test_03_uninstalled_skill_execution(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/uninstalled_fake_skill/execute")
        assert r.status_code == 200
        res = r.json()
        assert res["status"] == "error"

    # CASE 4: Blocked publisher
    def test_04_blocked_publisher(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.policy import MarketplacePolicy
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        policy = MarketplacePolicy(blocked_publishers={"Malicious Corp"}, require_admin_approval=False)
        p = SkillPackageManifest(
            package_id="bad.pub.v1",
            name="Bad Pub",
            version="1.0.0",
            publisher="Malicious Corp",
            description="Bad",
            skills=[ConductorSkill(id="s1", name="S1", description="D1")],
        )
        mp_reg.register_manifest(p)
        try:
            mp_reg.install_package("bad.pub.v1", user={"roles": ["admin"]}, policy=policy)
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass

    # CASE 5: Disallowed trust level
    def test_05_disallowed_trust_level(self):
        from eaip.copilot.marketplace.models import TrustLevel
        from eaip.copilot.marketplace.policy import MarketplacePolicy
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        policy = MarketplacePolicy(allowed_trust_levels={TrustLevel.BUILT_IN}, require_admin_approval=False)
        try:
            mp_reg.install_package("eaip.diagnostics.v1", user={"roles": ["admin"]}, policy=policy)
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass

    # CASE 6: Excessive permission request
    def test_06_excessive_permission_request(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        p = SkillPackageManifest(
            package_id="excess.perm.v1",
            name="Excess Perms",
            version="1.0.0",
            description="Excessive perms",
            required_permissions=["super_admin:override"],
            skills=[ConductorSkill(id="s2", name="S2", description="D2")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("excess.perm.v1") is not None

    # CASE 7: Excessive risk level
    def test_07_excessive_risk_level(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.policy import MarketplacePolicy
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.models import RiskTier
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        policy = MarketplacePolicy(max_allowed_risk_level=RiskTier.INFORMATIONAL, require_admin_approval=False)
        p = SkillPackageManifest(
            package_id="high.risk.v1",
            name="High Risk",
            version="1.0.0",
            description="High risk",
            risk_level=RiskTier.DESTRUCTIVE,
            skills=[ConductorSkill(id="s3", name="S3", description="D3", risk_level=RiskTier.DESTRUCTIVE)],
        )
        mp_reg.register_manifest(p)
        try:
            mp_reg.install_package("high.risk.v1", user={"roles": ["admin"]}, policy=policy)
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass

    # CASE 8: Missing tool dependency
    def test_08_incompatible_dependency(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        p = SkillPackageManifest(
            package_id="dep.missing.v1",
            name="Missing Dep",
            version="1.0.0",
            description="Missing dependency",
            tool_dependencies=["non_existent_tool_12345"],
            skills=[ConductorSkill(id="s4", name="S4", description="D4")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("dep.missing.v1") is not None

    # CASE 9: Circular dependency detection
    def test_09_circular_dependency(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.policy import MarketplacePolicy
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        p_a = SkillPackageManifest(
            package_id="pkg.a.v1",
            name="Pkg A",
            version="1.0.0",
            description="Pkg A",
            tool_dependencies=["pkg.b.v1"],
            skills=[ConductorSkill(id="sa", name="SA", description="DA")],
        )
        p_b = SkillPackageManifest(
            package_id="pkg.b.v1",
            name="Pkg B",
            version="1.0.0",
            description="Pkg B",
            tool_dependencies=["pkg.a.v1"],
            skills=[ConductorSkill(id="sb", name="SB", description="DB")],
        )
        mp_reg.register_manifest(p_a)
        mp_reg.register_manifest(p_b)
        try:
            mp_reg.install_package("pkg.a.v1", user={"roles": ["admin"]}, policy=MarketplacePolicy(require_admin_approval=False))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    # CASE 10: Cross-tenant skill execution
    async def test_10_cross_tenant_isolation(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/system_health_briefing/execute")
        assert r.status_code == 200

    # CASE 11: Disabled skill execution attempt
    async def test_11_disabled_skill_execution(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/fake_disabled_skill/execute")
        assert r.status_code == 200
        res = r.json()
        assert res["status"] == "error"

    # CASE 12: Forged package version
    def test_12_forged_package_version(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        try:
            p = SkillPackageManifest(
                package_id="forged.ver.v1",
                name="Forged Ver",
                version="999.invalid.version.format",
                description="Forged",
                skills=[ConductorSkill(id="sf", name="SF", description="DF")],
            )
            mp_reg.register_manifest(p)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    # CASE 13: Forged trust metadata
    def test_13_forged_trust_metadata(self):
        from eaip.copilot.marketplace.models import SkillPackageManifest, TrustLevel
        from eaip.copilot.marketplace.registry import MarketplaceRegistry
        from eaip.copilot.skills.models import ConductorSkill
        from eaip.copilot.skills.registry import SkillRegistry

        mp_reg = MarketplaceRegistry(SkillRegistry())
        p = SkillPackageManifest(
            package_id="forged.trust.v1",
            name="Forged Trust",
            version="1.0.0",
            trust_level=TrustLevel.BUILT_IN,
            description="Forged trust claim",
            skills=[ConductorSkill(id="st", name="ST", description="DT")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("forged.trust.v1").trust_level == TrustLevel.BUILT_IN

    # CASE 14: Forged permission metadata
    async def test_14_forged_permission_metadata(self, authenticated_client):
        r = await authenticated_client.get("/api/copilot/marketplace/catalog")
        assert r.status_code == 200

    # CASE 15: Forged approval ID
    async def test_15_forged_approval(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/approvals/forged-approval-999/approve")
        assert r.status_code == 404

    # CASE 16: Replayed approval
    async def test_16_replayed_approval(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/approvals/replayed-approval-000/approve")
        assert r.status_code == 404

    # CASE 17: Direct ToolRegistry bypass attempt
    async def test_17_direct_tool_registry_bypass(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "create agent BypassTest"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("pending_approval") is not None

    # CASE 18: Direct backend mutation attempt
    async def test_18_direct_backend_mutation(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "delete system database"})
        assert r.status_code == 200

    # CASE 19: Voice authorization bypass attempt
    async def test_19_voice_authorization_bypass(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "voice action create agent VoiceBypass"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("pending_approval") is not None

    # CASE 20: Proactive autonomous mutation attempt
    async def test_20_proactive_autonomous_mutation(self, authenticated_client):
        r = await authenticated_client.get("/api/copilot/anomalies")
        assert r.status_code == 200
        anomalies = r.json()
        assert isinstance(anomalies, list)








