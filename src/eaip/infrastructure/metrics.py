"""Default :class:`MetricsProvider` implementation — in-memory metrics store.

All metric types are thread-safe via ``threading.Lock``.  Data is kept
in-process; a future Prometheus or OTel adapter would implement the same
:class:`MetricsProvider` protocol.
"""

from __future__ import annotations

import threading
from typing import Any

from eaip.ports.metrics import Counter, Gauge, Histogram, MetricsProvider, Timer


class _InMemoryCounter(Counter):
    def __init__(self) -> None:
        self._value = 0.0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def get(self) -> float:
        with self._lock:
            return self._value


class _InMemoryGauge(Gauge):
    def __init__(self) -> None:
        self._value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value -= amount

    def get(self) -> float:
        with self._lock:
            return self._value


class _InMemoryHistogram(Histogram):
    def __init__(self, buckets: tuple[float, ...] | None = None) -> None:
        self._buckets = buckets or (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        self._counts: dict[str, int] = {str(b): 0 for b in self._buckets}
        self._counts["+Inf"] = 0
        self._total_count = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._total_count += 1
            for b in self._buckets:
                if value <= b:
                    self._counts[str(b)] += 1
                    return
            self._counts["+Inf"] += 1

    def get_bucket_counts(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counts)


class _InMemoryTimer(Timer):
    def __init__(self) -> None:
        self._count = 0
        self._total = 0.0
        self._lock = threading.Lock()

    def record(self, seconds: float) -> None:
        with self._lock:
            self._count += 1
            self._total += seconds

    def get_count(self) -> int:
        with self._lock:
            return self._count

    def get_total(self) -> float:
        with self._lock:
            return self._total

    def get_avg(self) -> float:
        with self._lock:
            return self._total / self._count if self._count > 0 else 0.0

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return {
                "count": self._count,
                "total": self._total,
                "avg": self._total / self._count if self._count > 0 else 0.0,
            }


class InMemoryMetricsProvider(MetricsProvider):
    """In-memory metrics provider that stores all metric data in-process."""

    def __init__(self) -> None:
        self._counters: dict[str, _InMemoryCounter] = {}
        self._gauges: dict[str, _InMemoryGauge] = {}
        self._histograms: dict[str, _InMemoryHistogram] = {}
        self._timers: dict[str, _InMemoryTimer] = {}
        self._lock = threading.Lock()

    def _key(self, name: str, labels: dict[str, str] | None = None) -> str:
        if labels:
            parts = [f"{k}={v}" for k, v in sorted(labels.items())]
            return f"{name}[{','.join(parts)}]"
        return name

    def counter(self, name: str, labels: dict[str, str] | None = None) -> Counter:
        k = self._key(name, labels)
        with self._lock:
            if k not in self._counters:
                self._counters[k] = _InMemoryCounter()
            return self._counters[k]

    def gauge(self, name: str, labels: dict[str, str] | None = None) -> Gauge:
        k = self._key(name, labels)
        with self._lock:
            if k not in self._gauges:
                self._gauges[k] = _InMemoryGauge()
            return self._gauges[k]

    def histogram(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram:
        k = self._key(name, labels)
        with self._lock:
            if k not in self._histograms:
                self._histograms[k] = _InMemoryHistogram(buckets)
            return self._histograms[k]

    def timer(self, name: str, labels: dict[str, str] | None = None) -> Timer:
        k = self._key(name, labels)
        with self._lock:
            if k not in self._timers:
                self._timers[k] = _InMemoryTimer()
            return self._timers[k]

    def get_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": {k: v.get() for k, v in self._counters.items()},
                "gauges": {k: v.get() for k, v in self._gauges.items()},
                "histograms": {k: v.get_bucket_counts() for k, v in self._histograms.items()},
                "timers": {k: v.snapshot() for k, v in self._timers.items()},
            }


__all__ = ["InMemoryMetricsProvider"]
