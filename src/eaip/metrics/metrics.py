"""Thread-safe metric primitives: Counter, Gauge, Histogram, Meter."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


@dataclass
class MetricBase:
    """Base dataclass for all metric types."""

    name: str
    description: str = ""
    unit: str = ""
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class Counter(MetricBase):
    """A monotonically increasing counter metric."""

    _value: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def inc(self, amount: int = 1) -> None:
        """Increment the counter by *amount* (must be non-negative)."""
        if amount < 0:
            raise ValueError("counter cannot decrement")
        with self._lock:
            self._value += amount

    @property
    def value(self) -> int:
        """Return the current counter value."""
        with self._lock:
            return self._value


@dataclass
class Gauge(MetricBase):
    """A gauge metric that can be set, incremented, or decremented."""

    _value: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, value: float) -> None:
        """Set the gauge to an absolute value."""
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increase the gauge by *amount*."""
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrease the gauge by *amount*."""
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> float:
        """Return the current gauge value."""
        with self._lock:
            return self._value


@dataclass
class Histogram(MetricBase):
    """A histogram metric that observes float values into configurable buckets."""

    buckets: tuple[float, ...] = _DEFAULT_BUCKETS
    _counts: list[int] = field(default_factory=list)
    _total: int = 0
    _sum: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        """Initialise per-bucket counters."""
        self._counts = [0] * (len(self.buckets) + 1)

    def observe(self, value: float) -> None:
        """Record an observation (must be non-negative)."""
        if value < 0:
            raise ValueError("histogram values must be non-negative")
        with self._lock:
            self._sum += value
            self._total += 1
            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self._counts[i] += 1
            self._counts[-1] += 1


class Meter:
    """A metric registry that creates and caches Counter, Gauge, and Histogram instances."""

    def __init__(self, *, namespace: str = "eaip") -> None:
        """Initialise the meter with an optional namespace."""
        self._namespace = namespace
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.RLock()

    @property
    def namespace(self) -> str:
        """Return the namespace for all metrics created by this meter."""
        return self._namespace

    def counter(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        labels: dict[str, str] | None = None,
    ) -> Counter:
        """Return or create a named counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(
                    name=name,
                    description=description,
                    unit=unit,
                    labels=labels or {},
                )
            return self._counters[name]

    def gauge(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        labels: dict[str, str] | None = None,
    ) -> Gauge:
        """Return or create a named gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(
                    name=name,
                    description=description,
                    unit=unit,
                    labels=labels or {},
                )
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        buckets: tuple[float, ...] = _DEFAULT_BUCKETS,
        labels: dict[str, str] | None = None,
    ) -> Histogram:
        """Return or create a named histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name=name,
                    description=description,
                    unit=unit,
                    buckets=buckets,
                    labels=labels or {},
                )
            return self._histograms[name]

    def collect(self) -> list[MetricBase]:
        """Return a snapshot of all registered metrics."""
        with self._lock:
            return [
                *list(self._counters.values()),
                *list(self._gauges.values()),
                *list(self._histograms.values()),
            ]
