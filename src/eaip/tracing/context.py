"""OTel context bridge — propagates trace context into RuntimeContext."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace

from eaip.runtime.context import RuntimeContext, current_context, scoped_runtime_context


def current_trace_context() -> dict[str, str]:
    """Extract trace_id and span_id from the current OTel span.

    Returns:
        A dict with ``trace_id`` and ``span_id`` (hex-encoded), or empty dict
        if no span is active.
    """
    span = trace.get_current_span()
    span_context = span.get_span_context()
    if not span_context.is_valid:
        return {}
    return {
        "trace_id": format(span_context.trace_id, "032x"),
        "span_id": format(span_context.span_id, "016x"),
    }


@contextmanager
def scoped_telemetry_context(
    labels: dict[str, str] | None = None,
    **kwargs: str,
) -> Iterator[RuntimeContext]:
    """Context manager that merges OTel trace context into the runtime context.

    Automatically enriches ``RuntimeContext`` with the current OTel trace_id
    and span_id. Additional keyword arguments are forwarded to
    :func:`scoped_runtime_context`.

    Usage::

        with scoped_telemetry_context(tenant_id="acme"):
            ctx = current_context()
            assert ctx.labels.get("trace_id") is not None
    """
    trace_ctx = current_trace_context()
    merged = {**(labels or {}), **trace_ctx}
    with scoped_runtime_context(labels=merged, **kwargs):
        yield current_context()


__all__ = ["current_trace_context", "scoped_telemetry_context"]
