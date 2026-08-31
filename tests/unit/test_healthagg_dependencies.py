"""Tests for DependencyGraph."""

from __future__ import annotations

from eaip.healthagg.dependencies import DependencyGraph


class TestDependencyGraph:
    def test_register_dependency(self) -> None:
        g = DependencyGraph()
        dep = g.register_dependency("api", "db", "hard")
        assert dep.id == "api->db"
        assert dep.source_component == "api"
        assert dep.target_component == "db"

    def test_register_dependency_defaults(self) -> None:
        g = DependencyGraph()
        dep = g.register_dependency("api", "db")
        assert dep.dependency_type == "hard"
        assert dep.optional is False
        assert dep.metadata == {}

    def test_register_dependency_with_metadata(self) -> None:
        g = DependencyGraph()
        dep = g.register_dependency("api", "db", "soft", optional=True, metadata={"latency": "5ms"})
        assert dep.optional is True
        assert dep.metadata == {"latency": "5ms"}

    async def test_build_graph_empty(self) -> None:
        g = DependencyGraph()
        graph = await g.build_graph()
        assert graph == {}

    async def test_build_graph(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        g.register_dependency("api", "cache", "soft")
        g.register_dependency("web", "api", "hard")
        graph = await g.build_graph()
        assert graph == {
            "api": {"db", "cache"},
            "db": set(),
            "cache": set(),
            "web": {"api"},
        }

    async def test_evaluate_impact_no_dependents(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        # db has api as a dependent; evaluate_impact on db returns api
        affected = await g.evaluate_impact("db")
        assert affected == ["api"]

    async def test_evaluate_impact_downstream(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        g.register_dependency("web", "api", "hard")
        g.register_dependency("web", "cache", "hard")
        affected = await g.evaluate_impact("db")
        assert "api" in affected
        assert "web" in affected

    async def test_evaluate_impact_skips_optional(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard", optional=True)
        g.register_dependency("web", "api", "hard")
        affected = await g.evaluate_impact("db")
        assert affected == []

    async def test_get_upstream_dependencies(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        g.register_dependency("api", "cache", "soft")
        g.register_dependency("web", "api", "hard")
        upstream = await g.get_upstream_dependencies("api")
        assert len(upstream) == 2

    async def test_get_upstream_dependencies_empty(self) -> None:
        g = DependencyGraph()
        upstream = await g.get_upstream_dependencies("nonexistent")
        assert upstream == []

    async def test_get_downstream_dependents(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        g.register_dependency("web", "api", "hard")
        downstream = await g.get_downstream_dependents("api")
        assert len(downstream) == 1
        assert downstream[0].source_component == "web"

    async def test_get_downstream_dependents_empty(self) -> None:
        g = DependencyGraph()
        downstream = await g.get_downstream_dependents("nonexistent")
        assert downstream == []

    async def test_get_critical_path(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "hard")
        g.register_dependency("web", "api", "hard")
        g.register_dependency("api", "cache", "soft")
        path = await g.get_critical_path("web")
        assert path == ["web", "api", "db"]

    async def test_get_critical_path_no_hard(self) -> None:
        g = DependencyGraph()
        g.register_dependency("api", "db", "soft")
        path = await g.get_critical_path("api")
        assert path == ["api"]

    async def test_get_critical_path_cycle(self) -> None:
        g = DependencyGraph()
        g.register_dependency("a", "b", "hard")
        g.register_dependency("b", "a", "hard")
        path = await g.get_critical_path("a")
        assert len(path) == 2
        assert path[0] == "a"
        assert path[1] == "b"
