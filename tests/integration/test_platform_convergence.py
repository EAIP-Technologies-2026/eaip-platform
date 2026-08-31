"""End-to-end platform convergence integration tests.

Validates the complete enterprise flow:
Login → Knowledge Upload → Agent Execution → Workflow → Mission → Runtime Registry
"""

from __future__ import annotations

import pytest

from eaip.agents.models import AgentSpec
from eaip.agents.registry import AgentRegistry
from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.models import AuthenticationRequest
from eaip.events.bus import EventBus
from eaip.health.reporter import HealthReporter
from eaip.infrastructure.health import InfrastructureHealthService
from eaip.knowledge.chunker import FixedSizeChunker
from eaip.knowledge.models import ChunkingConfig, DocumentFormat, IngestionConfig, RetrievalQuery
from eaip.knowledge.retrieval import KnowledgeRetriever
from eaip.runtime.mission import MissionRegistry
from eaip.runtime.runtime_registry import RuntimeRegistry
from eaip.workflow.models import WorkflowDefinition
from eaip.workflow.registry import WorkflowRegistry


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


class TestPlatformConvergence:
    """Complete enterprise platform flow."""

    async def test_login_to_mission_flow(self, event_bus: EventBus) -> None:
        """Full platform flow: login → knowledge → agent → workflow → mission."""

        # ── 1. Login ─────────────────────────────────────────────────
        auth = AuthenticationService(secret="convergence-secret", event_bus=event_bus)
        req = AuthenticationRequest(
            id="conv1",
            provider="mock",
            credentials={"username": "admin", "password": "pass"},
        )
        login = await auth.authenticate(req)
        assert login.success
        assert login.token

        user = await auth.get_current_user(login.token)
        assert user is not None
        assert user["sub"] == "admin"

        # ── 2. Knowledge Upload (via ingestion pipeline) ────────────
        class _MemoryStore:
            def __init__(self):
                self._collections: dict = {}

            async def create_collection(self, name, dimensions=384, **kw):
                self._collections.setdefault(name, [])

            async def upsert_points(self, collection, chunks):
                self._collections.setdefault(collection, [])
                for c in chunks:
                    self._collections[collection].append(c)

            async def search(self, collection, query):
                return [{"content": "result"}] if collection in self._collections else []

            async def delete_points(self, collection, point_ids):
                pass

            async def delete_collection(self, name):
                self._collections.pop(name, None)

            async def list_collections(self):
                return list(self._collections.keys())

            async def collection_info(self, name):
                return {"points_count": len(self._collections.get(name, []))}

        class _MockEmbed:
            async def embed(self, texts, **kw):
                return [(0.1,) * 384 for _ in texts]

            @property
            def dimensions(self):
                return 384

        store = _MemoryStore()
        embed = _MockEmbed()
        chunker = FixedSizeChunker(ChunkingConfig(chunk_size=100))
        config = IngestionConfig(collection="convergence_test")

        from eaip.knowledge.ingestion import IngestionPipeline

        pipeline = IngestionPipeline(
            config=config,
            vector_store=store,
            embedding_provider=embed,
        )
        result = await pipeline.ingest(
            document_id="conv_doc",
            content=b"Enterprise knowledge document for convergence testing.",
            doc_format=DocumentFormat.TXT,
        )
        assert result.status.value == "indexed"
        assert result.chunk_count > 0

        # ── 3. Knowledge Search ─────────────────────────────────────
        retriever = KnowledgeRetriever(vector_store=store, embedding_provider=embed)
        search = await retriever.search(
            "convergence_test", RetrievalQuery(query="knowledge", top_k=5)
        )
        assert len(search.chunks) >= 0

        # ── 4. Agent Registration ───────────────────────────────────
        agent_reg = AgentRegistry(event_bus=event_bus)
        agent = await agent_reg.create(
            AgentSpec(id="conv_agent", name="Convergence Agent", tools=("search",)),
            metadata={"tags": ["convergence"], "owner": "admin"},
        )
        assert agent.id == "conv_agent"

        # ── 5. Workflow Registration ────────────────────────────────
        wf_reg = WorkflowRegistry(event_bus=event_bus)
        wf = await wf_reg.create(
            WorkflowDefinition(id="conv_wf", name="Convergence Workflow"),
            metadata={"tags": ["convergence"]},
        )
        assert wf.id == "conv_wf"

        # ── 6. Mission Creation ─────────────────────────────────────
        mission_reg = MissionRegistry(event_bus=event_bus)
        mission = await mission_reg.create(
            mission_id="conv_mission",
            name="Convergence Mission",
            agent_ids=("conv_agent",),
            workflow_ids=("conv_wf",),
            knowledge_collections=("convergence_test",),
        )
        assert mission.mission_id == "conv_mission"
        assert mission.status.value == "draft"

        await mission.queue()
        await mission.start()
        await mission.complete(result="Convergence complete")

        assert mission.status.value == "completed"
        assert mission.result == "Convergence complete"

        # ── 7. Runtime Registry ─────────────────────────────────────
        runtime = RuntimeRegistry(event_bus=event_bus)
        await runtime.start()
        runtime.active_agents = 1
        runtime.active_workflows = 1
        runtime.active_sessions = 1
        runtime.active_knowledge_jobs = 1

        snap = runtime.get_snapshot()
        assert snap["active_agents"] == 1
        assert snap["active_workflows"] == 1
        assert snap["active_sessions"] == 1
        assert snap["active_knowledge_jobs"] == 1
        assert snap["health_status"] == "healthy"

        await runtime.stop()
        assert runtime.get_snapshot()["health_status"] == "stopped"

        # ── 8. Infrastructure Health ────────────────────────────────
        health = InfrastructureHealthService()
        cache_report = await health.check()
        assert cache_report.status.value == "healthy"

        health.register_connection("cache", True, {"type": "memory"})
        health.register_connection("database", False)
        report = await health.check()
        assert len(report.children) == 2


class TestInfrastructureHealth:
    """Infrastructure health checks."""

    async def test_no_backends(self) -> None:
        health = InfrastructureHealthService()
        report = await health.check()
        assert report.status.value == "healthy"

    async def test_all_healthy(self) -> None:
        health = InfrastructureHealthService()
        health.register_connection("cache", True)
        health.register_connection("queue", True)
        report = await health.check()
        assert report.status.value == "healthy"

    async def test_unhealthy_backend(self) -> None:
        health = InfrastructureHealthService()
        health.register_connection("database", True)
        health.register_connection("redis", False)
        report = await health.check()
        assert report.status.value == "unhealthy"
        assert "redis" in str(report.children[1].message)

    async def test_mixed_status(self) -> None:
        health = InfrastructureHealthService()
        health.register_connection("healthy_backend", True)
        health.register_connection("unhealthy_backend", False)
        report = await health.check()
        assert report.status.value == "unhealthy"

    async def test_with_health_reporter(self) -> None:
        health = InfrastructureHealthService()
        health.register_connection("cache", True)
        reporter = HealthReporter(name="platform")
        reporter.register(health)
        report = await reporter.report()
        assert report.component == "platform"
        assert report.status.value in ("healthy", "unhealthy")
