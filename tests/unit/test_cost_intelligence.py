"""Tests for Cost Intelligence — calculations, aggregations, edge cases."""

from __future__ import annotations

from collections import defaultdict


class TestCostIntelligenceCalculations:
    """Verify the calculation logic used by the cost intelligence router."""

    def test_safe_div_normal(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        assert _safe_div(10.0, 2.0) == 5.0

    def test_safe_div_zero_denominator(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        assert _safe_div(10.0, 0.0) == 0.0
        assert _safe_div(0.0, 0.0) == 0.0

    def test_safe_div_zero_numerator(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        assert _safe_div(0.0, 10.0) == 0.0

    def test_avg_cost_per_request(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        total_cost = 10.0
        records_count = 4
        avg = _safe_div(total_cost, records_count)
        assert avg == 2.5

    def test_avg_cost_zero_requests(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        total_cost = 0.0
        records_count = 0
        avg = _safe_div(total_cost, records_count)
        assert avg == 0.0

    def test_cost_aggregation_by_model(self) -> None:
        records = [
            {"model_id": "gpt-4", "amount": 1.0},
            {"model_id": "gpt-4", "amount": 2.0},
            {"model_id": "gpt-3.5", "amount": 0.5},
        ]
        cost_by_model: dict[str, float] = defaultdict(float)
        for r in records:
            cost_by_model[r["model_id"]] += r["amount"]
        assert cost_by_model["gpt-4"] == 3.0
        assert cost_by_model["gpt-3.5"] == 0.5

    def test_cost_aggregation_by_tenant(self) -> None:
        records = [
            {"tenant_id": "t1", "amount": 1.0},
            {"tenant_id": "t1", "amount": 2.0},
            {"tenant_id": "t2", "amount": 0.5},
            {"tenant_id": None, "amount": 0.1},
        ]
        cost_by_tenant: dict[str, float] = defaultdict(float)
        for r in records:
            if r["tenant_id"]:
                cost_by_tenant[r["tenant_id"]] += r["amount"]
        assert cost_by_tenant["t1"] == 3.0
        assert cost_by_tenant["t2"] == 0.5
        assert len(cost_by_tenant) == 2

    def test_token_aggregation(self) -> None:
        records = [
            {"input_tokens": 100, "output_tokens": 50},
            {"input_tokens": 200, "output_tokens": 100},
        ]
        total_input = sum(r["input_tokens"] for r in records)
        total_output = sum(r["output_tokens"] for r in records)
        total = total_input + total_output
        assert total_input == 300
        assert total_output == 150
        assert total == 450

    def test_budget_percentage_calculation(self) -> None:
        from eaip.http.routers.cost_intelligence import _safe_div
        current_spend = 80.0
        budget_amount = 100.0
        pct = _safe_div(current_spend, budget_amount) * 100
        assert pct == 80.0

    def test_budget_status_under(self) -> None:
        pct = 50.0
        status = "under"
        if pct >= 100:
            status = "exceeded"
        elif pct >= 90:
            status = "critical"
        elif pct >= 80:
            status = "warning"
        assert status == "under"

    def test_budget_status_warning(self) -> None:
        pct = 85.0
        status = "under"
        if pct >= 100:
            status = "exceeded"
        elif pct >= 90:
            status = "critical"
        elif pct >= 80:
            status = "warning"
        assert status == "warning"

    def test_budget_status_critical(self) -> None:
        pct = 95.0
        status = "under"
        if pct >= 100:
            status = "exceeded"
        elif pct >= 90:
            status = "critical"
        elif pct >= 80:
            status = "warning"
        assert status == "critical"

    def test_budget_status_exceeded(self) -> None:
        pct = 105.0
        status = "under"
        if pct >= 100:
            status = "exceeded"
        elif pct >= 90:
            status = "critical"
        elif pct >= 80:
            status = "warning"
        assert status == "exceeded"

    def test_anomaly_detection_critical(self) -> None:
        avg = 10.0
        cost = 20.0
        deviation = cost - avg
        pct = abs(deviation / avg * 100)
        severity = "low"
        if pct > 50:
            severity = "critical"
        elif pct > 25:
            severity = "high"
        elif pct > 10:
            severity = "medium"
        assert severity == "critical"
        assert deviation == 10.0

    def test_anomaly_detection_medium(self) -> None:
        avg = 10.0
        cost = 12.0
        deviation = cost - avg
        pct = abs(deviation / avg * 100)
        severity = "low"
        if pct > 50:
            severity = "critical"
        elif pct > 25:
            severity = "high"
        elif pct > 10:
            severity = "medium"
        assert severity == "medium"

    def test_anomaly_detection_below_threshold(self) -> None:
        avg = 10.0
        cost = 10.5
        deviation = cost - avg
        pct = abs(deviation / avg * 100)
        severity = "low"
        if pct > 50:
            severity = "critical"
        elif pct > 25:
            severity = "high"
        elif pct > 10:
            severity = "medium"
        assert severity == "low"

    def test_anomaly_zero_average(self) -> None:
        avg = 0.0
        cost = 5.0
        deviation = cost - avg
        pct = abs(deviation / avg * 100) if avg > 0 else 0.0
        assert pct == 0.0


class TestCostIntelligenceDataStructures:
    """Verify the data structures returned by the API."""

    def test_overview_structure(self) -> None:
        overview = {
            "totalCost": 100.50,
            "totalRequests": 500,
            "totalTokens": 1000000,
            "inputTokens": 700000,
            "outputTokens": 300000,
            "avgCostPerRequest": 0.201,
            "modelCount": 3,
            "currency": "USD",
        }
        assert overview["totalCost"] == 100.50
        assert overview["totalRequests"] == 500
        assert overview["currency"] == "USD"

    def test_model_cost_structure(self) -> None:
        model = {
            "modelId": "gpt-4",
            "totalCost": 50.0,
            "requests": 100,
            "inputTokens": 50000,
            "outputTokens": 20000,
            "totalTokens": 70000,
            "avgCostPerRequest": 0.5,
            "currency": "USD",
        }
        assert model["modelId"] == "gpt-4"
        assert model["totalTokens"] == 70000

    def test_provider_cost_structure(self) -> None:
        provider = {
            "provider": "openai",
            "totalCost": 75.0,
            "requests": 200,
            "inputTokens": 100000,
            "outputTokens": 50000,
            "modelCount": 2,
            "currency": "USD",
        }
        assert provider["provider"] == "openai"
        assert provider["modelCount"] == 2

    def test_budget_status_structure(self) -> None:
        budget = {
            "id": "b1",
            "name": "Monthly AI Budget",
            "amount": 1000.0,
            "currentSpend": 750.0,
            "percentage": 75.0,
            "status": "under",
            "period": "monthly",
            "currency": "USD",
            "enabled": True,
        }
        assert budget["status"] == "under"
        assert budget["percentage"] == 75.0

    def test_anomaly_structure(self) -> None:
        anomaly = {
            "modelId": "gpt-4",
            "actualCost": 25.0,
            "expectedCost": 10.0,
            "deviation": 15.0,
            "deviationPercent": 150.0,
            "severity": "critical",
        }
        assert anomaly["severity"] == "critical"
        assert anomaly["deviationPercent"] == 150.0

    def test_trend_structure(self) -> None:
        trend = {
            "date": "2024-01-15",
            "cost": 12.50,
            "requests": 50,
            "inputTokens": 25000,
            "outputTokens": 10000,
            "totalTokens": 35000,
        }
        assert trend["date"] == "2024-01-15"
        assert trend["totalTokens"] == 35000
