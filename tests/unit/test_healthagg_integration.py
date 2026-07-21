"""Tests for HealthAggRuntimeModule."""

from __future__ import annotations

from eaip.healthagg.aggregator import HealthAggregator
from eaip.healthagg.dependencies import DependencyGraph
from eaip.healthagg.integration import HealthAggRuntimeModule
from eaip.healthagg.models import HealthAggregationConfig
from eaip.healthagg.status_page import StatusPageService


class TestHealthAggRuntimeModule:
    def test_module_name(self) -> None:
        module = HealthAggRuntimeModule()
        assert module.name == "healthagg"

    def test_default_config(self) -> None:
        module = HealthAggRuntimeModule()
        assert module.config.aggregation_interval_seconds == 60
        assert module.config.dependency_graph_enabled is True

    def test_custom_config(self) -> None:
        config = HealthAggregationConfig(aggregation_interval_seconds=120)
        module = HealthAggRuntimeModule(config=config)
        assert module.config.aggregation_interval_seconds == 120

    def test_aggregator_property(self) -> None:
        module = HealthAggRuntimeModule()
        assert module.aggregator is not None
        assert isinstance(module.aggregator, HealthAggregator)

    def test_dependency_graph_property(self) -> None:
        module = HealthAggRuntimeModule()
        assert module.dependency_graph is not None
        assert isinstance(module.dependency_graph, DependencyGraph)

    def test_status_page_service_property(self) -> None:
        module = HealthAggRuntimeModule()
        assert module.status_page_service is not None
        assert isinstance(module.status_page_service, StatusPageService)

    def test_custom_dependencies(self) -> None:
        graph = DependencyGraph()
        agg = HealthAggregator()
        svc = StatusPageService()
        module = HealthAggRuntimeModule(
            dependency_graph=graph,
            aggregator=agg,
            status_page_service=svc,
        )
        assert module.dependency_graph is graph
        assert module.aggregator is agg
        assert module.status_page_service is svc
