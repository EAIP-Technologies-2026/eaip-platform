"""Metrics provider port — abstract metrics interface.

The :class:`MetricsProvider` protocol decouples platform services from any
specific metrics backend (in-memory, Prometheus, OpenTelemetry, etc.).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Counter(Protocol):
    """A monotonically-increasing counter."""

    def inc(self, amount: float = 1.0) -> None: ...
    def get(self) -> float: ...


@runtime_checkable
class Gauge(Protocol):
    """A gauge that can be set, incremented, and decremented."""

    def set(self, value: float) -> None: ...
    def inc(self, amount: float = 1.0) -> None: ...
    def dec(self, amount: float = 1.0) -> None: ...
    def get(self) -> float: ...


@runtime_checkable
class Histogram(Protocol):
    """A histogram observing values into configurable buckets."""

    def observe(self, value: float) -> None: ...
    def get_bucket_counts(self) -> dict[str, int]: ...


@runtime_checkable
class Timer(Protocol):
    """A timer that records duration."""

    def record(self, seconds: float) -> None: ...
    def get_count(self) -> int: ...
    def get_total(self) -> float: ...


@runtime_checkable
class MetricsProvider(Protocol):
    """Pluggable metrics backend contract."""

    def counter(self, name: str, labels: dict[str, str] | None = None) -> Counter: ...
    def gauge(self, name: str, labels: dict[str, str] | None = None) -> Gauge: ...
    def histogram(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram: ...
    def timer(self, name: str, labels: dict[str, str] | None = None) -> Timer: ...
    def get_snapshot(self) -> dict[str, Any]: ...


__all__ = ["Counter", "Gauge", "Histogram", "MetricsProvider", "Timer"]
