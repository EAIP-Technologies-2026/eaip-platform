from __future__ import annotations

import pytest

from eaip.metrics import Counter, Gauge, Histogram, Meter
from eaip.metrics.export import prometheus_text


class TestCounter:
    def test_default_value_is_zero(self):
        c = Counter(name="test")
        assert c.value == 0

    def test_inc_increases(self):
        c = Counter(name="test")
        c.inc()
        assert c.value == 1
        c.inc(5)
        assert c.value == 6

    def test_inc_negative_raises(self):
        c = Counter(name="test")
        with pytest.raises(ValueError, match="cannot decrement"):
            c.inc(-1)

    def test_labels_and_metadata(self):
        c = Counter(
            name="http_requests",
            description="Total HTTP requests",
            unit="count",
            labels={"method": "GET"},
        )
        assert c.name == "http_requests"
        assert c.description == "Total HTTP requests"
        assert c.labels == {"method": "GET"}


class TestGauge:
    def test_default_value_is_zero(self):
        g = Gauge(name="test")
        assert g.value == 0.0

    def test_set_and_modify(self):
        g = Gauge(name="test")
        g.set(42.5)
        assert g.value == 42.5
        g.inc(1.5)
        assert g.value == 44.0
        g.dec(2.0)
        assert g.value == 42.0

    def test_inc_with_default(self):
        g = Gauge(name="test")
        g.inc()
        assert g.value == 1.0


class TestHistogram:
    def test_observe_records(self):
        h = Histogram(name="latency", buckets=(0.1, 0.5, 1.0))
        h.observe(0.2)
        h.observe(0.6)
        h.observe(2.0)
        assert h._total == 3
        assert h._sum == pytest.approx(2.8)

    def test_negative_value_raises(self):
        h = Histogram(name="test")
        with pytest.raises(ValueError, match="non-negative"):
            h.observe(-1.0)

    def test_custom_buckets(self):
        h = Histogram(name="custom", buckets=(1.0, 5.0, 10.0))
        assert len(h._counts) == 4


class TestMeter:
    def test_counter_creates_once(self):
        m = Meter()
        c1 = m.counter("hits")
        c2 = m.counter("hits")
        assert c1 is c2

    def test_gauge_creates_once(self):
        m = Meter()
        g1 = m.gauge("temp")
        g2 = m.gauge("temp")
        assert g1 is g2

    def test_histogram_creates_once(self):
        m = Meter()
        h1 = m.histogram("latency")
        h2 = m.histogram("latency")
        assert h1 is h2

    def test_collect_returns_all_metrics(self):
        m = Meter()
        m.counter("a")
        m.gauge("b")
        m.histogram("c")
        collected = m.collect()
        assert len(collected) == 3

    def test_namespace_property(self):
        m = Meter(namespace="myapp")
        assert m.namespace == "myapp"


class TestPrometheusExport:
    def test_export_counter(self):
        c = Counter(name="requests_total", description="Total requests", labels={"method": "GET"})
        c.inc(3)
        output = prometheus_text([c])
        assert "# HELP requests_total Total requests" in output
        assert "# TYPE requests_total counter" in output
        assert 'requests_total{method="GET"} 3' in output

    def test_export_gauge(self):
        g = Gauge(name="memory_usage", description="Current memory usage")
        g.set(1024.5)
        output = prometheus_text([g])
        assert "# HELP memory_usage Current memory usage" in output
        assert "# TYPE memory_usage gauge" in output
        assert "memory_usage 1024.5" in output

    def test_export_histogram(self):
        h = Histogram(name="request_duration", description="Request duration", buckets=(0.1, 0.5))
        h.observe(0.05)
        h.observe(0.3)
        h.observe(1.0)
        output = prometheus_text([h])
        assert "# HELP request_duration Request duration" in output
        assert "# TYPE request_duration histogram" in output
        assert "request_duration_sum" in output
        assert "request_duration_count 3" in output

    def test_empty_metrics(self):
        output = prometheus_text([])
        assert output == "\n"
