"""Prometheus/OpenMetrics text-format export for EAIP metrics."""

from __future__ import annotations

from collections.abc import Iterable

from eaip.metrics.metrics import Counter, Gauge, Histogram, MetricBase


def _sanitise_name(name: str) -> str:
    return name.replace("-", "_").replace(".", "_").replace(" ", "_")


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = ", ".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return "{" + parts + "}"


def _export_counter(c: Counter) -> str:
    name = _sanitise_name(c.name)
    help_line = f"# HELP {name} {c.description}" if c.description else ""
    type_line = f"# TYPE {name} counter"
    labels = _format_labels(c.labels)
    value_line = f"{name}{labels} {c.value}"
    return "\n".join(filter(None, [help_line, type_line, value_line]))


def _export_gauge(g: Gauge) -> str:
    name = _sanitise_name(g.name)
    help_line = f"# HELP {name} {g.description}" if g.description else ""
    type_line = f"# TYPE {name} gauge"
    labels = _format_labels(g.labels)
    value_line = f"{name}{labels} {g.value}"
    return "\n".join(filter(None, [help_line, type_line, value_line]))


def _export_histogram(h: Histogram) -> str:
    name = _sanitise_name(h.name)
    lines: list[str] = []
    if h.description:
        lines.append(f"# HELP {name} {h.description}")
    lines.append(f"# TYPE {name} histogram")
    base_labels = _format_labels(h.labels)
    cumul = 0
    for i, bucket in enumerate(h.buckets):
        cumul += h._counts[i]
        bucket_labels = f'{{le="{bucket}"' + (", " + base_labels[1:-1] if base_labels else "")
        if base_labels:
            bucket_labels += ", " + base_labels[1:-1]
        bucket_labels += "}"
        lines.append(f"{name}_bucket{bucket_labels} {cumul}")
    total_labels = '{"le="+Inf"' + (", " + base_labels[1:-1] if base_labels else "")
    if base_labels:
        total_labels += ", " + base_labels[1:-1]
    total_labels += "}"
    lines.append(f"{name}_bucket{total_labels} {h._total}")
    lines.append(f"{name}_sum{base_labels} {h._sum}")
    lines.append(f"{name}_count{base_labels} {h._total}")
    return "\n".join(lines)


def prometheus_text(metrics: Iterable[MetricBase]) -> str:
    """Render metrics in Prometheus/OpenMetrics text format."""
    lines: list[str] = []
    for m in metrics:
        if isinstance(m, Counter):
            lines.append(_export_counter(m))
        elif isinstance(m, Gauge):
            lines.append(_export_gauge(m))
        elif isinstance(m, Histogram):
            lines.append(_export_histogram(m))
    return "\n\n".join(lines) + "\n"
