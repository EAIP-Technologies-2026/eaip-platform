"""No-op :class:`TracingProvider` implementation — discards all spans.

Use as the default when no external tracer (OpenTelemetry) is configured.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from eaip.ports.tracing import Span, TracingProvider


class _NoOpSpan(Span):
    def set_attribute(self, key: str, value: Any) -> None: ...
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None: ...
    def set_status(self, code: int, description: str = "") -> None: ...
    def end(self) -> None: ...


class NoOpTracingProvider(TracingProvider):
    """Tracing provider that discards every span — useful as a default."""

    def __init__(self) -> None:
        self._noop = _NoOpSpan()

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        return self._noop

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Generator[Span, None, None]:
        yield self._noop

    def inject(self, span: Span) -> dict[str, str]:
        return {}

    def current_span_id(self) -> str | None:
        return None

    def current_trace_id(self) -> str | None:
        return None


__all__ = ["NoOpTracingProvider"]
