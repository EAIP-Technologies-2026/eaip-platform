from __future__ import annotations

import pytest

from eaip.diagnostics.engine import DiagnosticsEngine, HealthProbe, ProbeStatus


class TestDiagnosticsEngine:
    @pytest.fixture
    def engine(self) -> DiagnosticsEngine:
        return DiagnosticsEngine()

    def test_register_probe(self, engine: DiagnosticsEngine) -> None:
        probe = HealthProbe(probe_id="p1", name="memory", check_fn=lambda: True)
        engine.register_probe(probe)
        assert engine.get_probe("p1") is not None

    def test_unregister_probe(self, engine: DiagnosticsEngine) -> None:
        probe = HealthProbe(probe_id="p1", name="memory", check_fn=lambda: True)
        engine.register_probe(probe)
        assert engine.unregister_probe("p1") is True
        assert engine.get_probe("p1") is None

    def test_list_probes(self, engine: DiagnosticsEngine) -> None:
        engine.register_probe(HealthProbe(probe_id="p1", name="a", check_fn=lambda: True))
        engine.register_probe(HealthProbe(probe_id="p2", name="b", check_fn=lambda: True))
        assert len(engine.list_probes()) == 2

    @pytest.mark.asyncio
    async def test_run_probe_pass(self, engine: DiagnosticsEngine) -> None:
        engine.register_probe(HealthProbe(probe_id="p1", name="test", check_fn=lambda: True))
        result = await engine.run_probe("p1")
        assert result.status == ProbeStatus.PASS

    @pytest.mark.asyncio
    async def test_run_probe_fail(self, engine: DiagnosticsEngine) -> None:
        engine.register_probe(HealthProbe(probe_id="p1", name="test", check_fn=lambda: False))
        result = await engine.run_probe("p1")
        assert result.status == ProbeStatus.FAIL

    @pytest.mark.asyncio
    async def test_run_probe_exception(self, engine: DiagnosticsEngine) -> None:
        def failing() -> bool:
            msg = "oops"
            raise RuntimeError(msg)

        engine.register_probe(HealthProbe(probe_id="p1", name="test", check_fn=failing))
        result = await engine.run_probe("p1")
        assert result.status == ProbeStatus.FAIL

    @pytest.mark.asyncio
    async def test_run_all_probes(self, engine: DiagnosticsEngine) -> None:
        engine.register_probe(HealthProbe(probe_id="p1", name="a", check_fn=lambda: True))
        engine.register_probe(HealthProbe(probe_id="p2", name="b", check_fn=lambda: True))
        results = await engine.run_all_probes()
        assert len(results) == 2

    def test_get_results(self, engine: DiagnosticsEngine) -> None:
        assert len(engine.get_results()) == 0

    def test_incident_created_on_failure(self, engine: DiagnosticsEngine) -> None:
        import asyncio

        probe = HealthProbe(probe_id="p1", name="test", check_fn=lambda: False)
        engine.register_probe(probe)
        asyncio.run(engine.run_probe("p1"))
        incidents = engine.get_incidents()
        assert len(incidents) == 1

    def test_resolve_incident(self, engine: DiagnosticsEngine) -> None:
        import asyncio

        probe = HealthProbe(probe_id="p1", name="test", check_fn=lambda: False)
        engine.register_probe(probe)
        asyncio.run(engine.run_probe("p1"))
        incidents = engine.get_incidents()
        assert len(incidents) == 1
        result = engine.resolve_incident(incidents[0].incident_id, "fixed")
        assert result is True
        assert engine.get_incidents(unresolved_only=True) == []
