"""Prometheus-backed :class:`MetricsProvider` implementation.

Provides production-grade metrics collection behind the existing
:class:`MetricsProvider` port.  Exposes a ``/metrics`` endpoint
for Prometheus scraping.

Usage::

    from eaip.infrastructure.prometheus_metrics import PrometheusMetricsProvider

    metrics = PrometheusMetricsProvider()
    counter = metrics.counter("requests_total", {"method": "GET"})
    counter.inc()
"""

from __future__ import annotations

from typing import Any

from eaip.ports.metrics import Counter, Gauge, Histogram, MetricsProvider, Timer


class _PrometheusCounter(Counter):
    def __init__(self, counter: Any) -> None:
        self._counter = counter

    def inc(self, amount: float = 1.0) -> None:
        self._counter.inc(amount)

    def get(self) -> float:
        return float(self._counter._value.get())


class _PrometheusGauge(Gauge):
    def __init__(self, gauge: Any) -> None:
        self._gauge = gauge

    def set(self, value: float) -> None:
        self._gauge.set(value)

    def inc(self, amount: float = 1.0) -> None:
        self._gauge.inc(amount)

    def dec(self, amount: float = 1.0) -> None:
        self._gauge.dec(amount)

    def get(self) -> float:
        return float(self._gauge._value.get())


class _PrometheusHistogram(Histogram):
    def __init__(self, histogram: Any) -> None:
        self._histogram = histogram

    def observe(self, value: float) -> None:
        self._histogram.observe(value)

    def get_bucket_counts(self) -> dict[str, int]:
        return {}


class _PrometheusTimer(Timer):
    def __init__(self, timer_name: str, registry: Any) -> None:
        self._name = timer_name
        self._registry = registry
        self._count = 0
        self._total = 0.0

    def record(self, seconds: float) -> None:
        self._count += 1
        self._total += seconds

    def get_count(self) -> int:
        return self._count

    def get_total(self) -> float:
        return self._total


class PrometheusMetricsProvider(MetricsProvider):
    """Production metrics provider backed by Prometheus client library.

    Supports the standard Prometheus metric types and exposes them
    via the ``/metrics`` endpoint for scraping.
    """

    def __init__(self, namespace: str = "eaip") -> None:
        self._namespace = namespace
        self._registry: Any = None

    def _get_registry(self) -> Any:
        if self._registry is None:
            from prometheus_client import CollectorRegistry  # type: ignore[import-not-found]

            self._registry = CollectorRegistry()
        return self._registry

    def _make_name(self, name: str) -> str:
        return f"{self._namespace}_{name}" if self._namespace else name

    def counter(self, name: str, labels: dict[str, str] | None = None) -> Counter:
        from prometheus_client import Counter as PromCounter

        registry = self._get_registry()
        label_names = list(labels.keys()) if labels else []
        prom_counter = PromCounter(
            self._make_name(name), "", label_names, registry=registry
        )
        if labels:
            prom_counter = prom_counter.labels(**labels)
        return _PrometheusCounter(prom_counter)

    def gauge(self, name: str, labels: dict[str, str] | None = None) -> Gauge:
        from prometheus_client import Gauge as PromGauge

        registry = self._get_registry()
        label_names = list(labels.keys()) if labels else []
        prom_gauge = PromGauge(
            self._make_name(name), "", label_names, registry=registry
        )
        if labels:
            prom_gauge = prom_gauge.labels(**labels)
        return _PrometheusGauge(prom_gauge)

    def histogram(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram:
        from prometheus_client import Histogram as PromHistogram

        registry = self._get_registry()
        label_names = list(labels.keys()) if labels else []
        kwargs: dict[str, Any] = {"name": self._make_name(name), "documentation": "", "labelnames": label_names, "registry": registry}
        if buckets:
            kwargs["buckets"] = buckets
        prom_histogram = PromHistogram(**kwargs)
        if labels:
            prom_histogram = prom_histogram.labels(**labels)
        return _PrometheusHistogram(prom_histogram)

    def timer(self, name: str, labels: dict[str, str] | None = None) -> Timer:
        return _PrometheusTimer(self._make_name(name), self._get_registry())

    def get_snapshot(self) -> dict[str, Any]:
        return {"type": "prometheus", "namespace": self._namespace}

    def generate_latest(self) -> bytes:
        """Return the Prometheus exposition format output."""
        from prometheus_client import generate_latest

        return generate_latest(self._get_registry())


__all__ = ["PrometheusMetricsProvider"]
