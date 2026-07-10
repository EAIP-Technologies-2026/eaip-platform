"""Tests for error budget."""

from __future__ import annotations

from eaip.resilience.error_budget import ErrorBudget, ErrorBudgetConfig


class TestErrorBudget:
    def test_initial_state(self) -> None:
        eb = ErrorBudget("test")
        assert eb.error_rate == 0.0
        assert eb.budget_remaining == 1.0
        assert not eb.is_exhausted

    def test_record_success(self) -> None:
        eb = ErrorBudget("test")
        eb.record_success()
        assert eb.error_rate == 0.0
        assert eb.total_requests > 0

    def test_record_error(self) -> None:
        eb = ErrorBudget("test")
        eb.record_error()
        assert eb.error_rate > 0.0
        assert eb.is_warning is False

    def test_budget_exhaustion(self) -> None:
        eb = ErrorBudget("test", ErrorBudgetConfig(max_error_rate=0.3))
        eb.record_success()  # 0 errors / 1 total = 0% error
        eb.record_error()     # 1 error / 2 total = 50% > 30% threshold
        eb.record_error()     # 2 errors / 3 total = 66% > 30% threshold
        assert eb.is_exhausted

    def test_budget_warning(self) -> None:
        eb = ErrorBudget("test", ErrorBudgetConfig(max_error_rate=0.5, warning_threshold=0.7))
        eb.record_success()
        eb.record_success()
        eb.record_success()
        eb.record_error()     # 1 error / 4 total = 25% < 50% threshold
        assert eb.error_rate == 0.25
        assert not eb.is_exhausted

    def test_get_metrics(self) -> None:
        eb = ErrorBudget("test")
        metrics = eb.get_metrics()
        assert metrics["name"] == "test"
        assert metrics["error_rate"] == 0.0
