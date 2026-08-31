"""Tracing provider port — abstract tracing interface.

The :class:`TracingProvider` protocol decouples platform services from any
specific tracing backend (in-memory, OpenTelemetry, etc.).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Span(Protocol):
    """A single tracing span."""

    def set_attribute(self, key: str, value: Any) -> None: ...
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None: ...
    def set_status(self, code: int, description: str = "") -> None: ...
    def end(self) -> None: ...


@runtime_checkable
class TracingProvider(Protocol):
    """Pluggable tracing backend contract."""

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span: ...

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]: ...

    def inject(self, span: Span) -> dict[str, str]:
        """Return carrier dict for propagation."""
        ...

    def current_span_id(self) -> str | None: ...
    def current_trace_id(self) -> str | None: ...


__all__ = ["Span", "TracingProvider"]
