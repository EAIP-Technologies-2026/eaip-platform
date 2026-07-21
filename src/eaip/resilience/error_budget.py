"""Error budget tracking for SLO-based reliability management."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from pydantic import BaseModel, ConfigDict

from eaip.logging.context import get_logger


class ErrorBudgetConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    budget_period_seconds: float = 86400.0
    max_error_rate: float = 0.01
    warning_threshold: float = 0.5


class ErrorBudget:
    """Error budget tracker for monitoring service reliability."""

    def __init__(
        self,
        name: str,
        config: ErrorBudgetConfig | None = None,
        *,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._name = name
        self._config = config or ErrorBudgetConfig()
        self._total_requests: int = 0
        self._error_count: int = 0
        self._recent_errors: deque[float] = deque()
        self._event_bus = event_bus
        self._meter = meter
        self._log = get_logger(f"eaip.resilience.error_budget.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def total_requests(self) -> int:
        return self._total_requests

    def record_success(self) -> None:
        self._total_requests += 1
        self._trim_window()

    def record_error(self) -> None:
        self._total_requests += 1
        self._error_count += 1
        self._recent_errors.append(time.monotonic())
        self._trim_window()

    def _trim_window(self) -> None:
        cutoff = time.monotonic() - self._config.budget_period_seconds
        while self._recent_errors and self._recent_errors[0] < cutoff:
            self._recent_errors.popleft()
            self._error_count = max(0, self._error_count - 1)

    @property
    def error_rate(self) -> float:
        if self._total_requests == 0:
            return 0.0
        return self._error_count / self._total_requests

    @property
    def budget_remaining(self) -> float:
        if self._total_requests == 0:
            return 1.0
        max_allowed = self._total_requests * self._config.max_error_rate
        if max_allowed <= 0:
            return 0.0
        consumed = self._error_count
        return max(0.0, (max_allowed - consumed) / max_allowed)

    @property
    def is_exhausted(self) -> bool:
        return self.budget_remaining <= 0.0

    @property
    def is_warning(self) -> bool:
        return 0.0 < self.budget_remaining <= self._config.warning_threshold

    def get_metrics(self) -> dict[str, object]:
        return {
            "name": self._name,
            "total_requests": self._total_requests,
            "error_count": self._error_count,
            "error_rate": round(self.error_rate, 6),
            "budget_remaining": round(self.budget_remaining, 4),
            "is_exhausted": self.is_exhausted,
        }


__all__ = [
    "ErrorBudget",
    "ErrorBudgetConfig",
]
