from __future__ import annotations

import pytest

from eaip.mesh.exceptions import MeshError
from eaip.mesh.model_router import ModelEndpoint, ModelRouter


class TestModelRouter:
    @pytest.fixture
    def router(self) -> ModelRouter:
        return ModelRouter()

    def test_register_and_route(self, router: ModelRouter) -> None:
        ep = ModelEndpoint(model_id="gpt4", provider="openai", endpoint="https://api.openai.com/v1")
        router.register_endpoint(ep)
        result = router.route("gpt4")
        assert result.model_id == "gpt4"
        assert result.provider == "openai"

    def test_route_to_nonexistent_model_raises(self, router: ModelRouter) -> None:
        with pytest.raises(MeshError):
            router.route("nonexistent")

    def test_weighted_distribution(self, router: ModelRouter) -> None:
        router.register_endpoint(
            ModelEndpoint(model_id="m1", provider="p1", endpoint="e1", weight=80)
        )
        router.register_endpoint(
            ModelEndpoint(model_id="m1", provider="p2", endpoint="e2", weight=20)
        )
        counts: dict[str, int] = {"e1": 0, "e2": 0}
        for _ in range(100):
            ep = router.route("m1")
            counts[ep.endpoint] += 1
        total = counts["e1"] + counts["e2"]
        assert total == 100
        assert counts["e1"] > counts["e2"]

    def test_route_with_preferred_provider(self, router: ModelRouter) -> None:
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p1", endpoint="e1"))
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p2", endpoint="e2"))
        result = router.route("m1", prefer_provider="p2")
        assert result.provider == "p2"

    def test_route_with_inactive_endpoints(self, router: ModelRouter) -> None:
        router.register_endpoint(
            ModelEndpoint(model_id="m1", provider="p1", endpoint="e1", is_active=False)
        )
        router.register_endpoint(
            ModelEndpoint(model_id="m1", provider="p2", endpoint="e2", is_active=True)
        )
        result = router.route("m1")
        assert result.endpoint == "e2"

    def test_all_endpoints_inactive_raises(self, router: ModelRouter) -> None:
        router.register_endpoint(
            ModelEndpoint(model_id="m1", provider="p1", endpoint="e1", is_active=False)
        )
        with pytest.raises(MeshError):
            router.route("m1")

    def test_mark_inactive_and_active(self, router: ModelRouter) -> None:
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p1", endpoint="e1"))
        router.mark_inactive("m1", "e1")
        result = router.health_check("m1")
        assert result["inactive_endpoints"] == 1
        router.mark_active("m1", "e1")
        result = router.health_check("m1")
        assert result["active_endpoints"] == 1

    def test_health_check(self, router: ModelRouter) -> None:
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p1", endpoint="e1"))
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p2", endpoint="e2"))
        result = router.health_check("m1")
        assert result["total_endpoints"] == 2
        assert result["active_endpoints"] == 2

    def test_report_latency_and_error(self, router: ModelRouter) -> None:
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p1", endpoint="e1"))
        router.report_latency("m1", "e1", 0.5)
        router.report_error("m1", "e1")
        hc = router.health_check("m1")
        ep = hc["endpoints"][0]
        assert ep["latency_p50"] > 0
        assert ep["error_rate"] > 0

    def test_route_weighted(self, router: ModelRouter) -> None:
        router.register_endpoint(
            ModelEndpoint(
                model_id="m1", provider="p1", endpoint="e1", latency_p50=0.1, error_rate=0.0
            )
        )
        router.register_endpoint(
            ModelEndpoint(
                model_id="m1", provider="p2", endpoint="e2", latency_p50=1.0, error_rate=0.5
            )
        )
        result = router.route_weighted("m1", {"p1": 10, "p2": 1})
        assert result.provider == "p1"

    def test_unregister_endpoint(self, router: ModelRouter) -> None:
        router.register_endpoint(ModelEndpoint(model_id="m1", provider="p1", endpoint="e1"))
        router.unregister_endpoint("m1", "e1")
        assert len(router.get_endpoints("m1")) == 0
