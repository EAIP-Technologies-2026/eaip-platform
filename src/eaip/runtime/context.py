"""Runtime context with contextvars support for run/correlation/tenant IDs."""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from eaip.shared.identifiers import CorrelationId, RunId

_current_context: contextvars.ContextVar[RuntimeContext | None] = contextvars.ContextVar(
    "_runtime_context", default=None
)


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Immutable runtime context carrying run, correlation, and tenant identifiers."""

    run_id: RunId | None = None
    correlation_id: CorrelationId | None = None
    tenant_id: str | None = None
    labels: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """Ensure labels is never None."""
        if self.labels is None:
            object.__setattr__(self, "labels", {})

    def with_(self, **kwargs: Any) -> RuntimeContext:
        """Return a new context with the given fields merged."""
        return RuntimeContext(
            run_id=kwargs.get("run_id", self.run_id),
            correlation_id=kwargs.get("correlation_id", self.correlation_id),
            tenant_id=kwargs.get("tenant_id", self.tenant_id),
            labels={**(self.labels or {}), **kwargs.get("labels", {})},
        )

    def bind(self) -> None:
        """Set this context as the current contextvar value."""
        _current_context.set(self)


def current_context() -> RuntimeContext:
    """Return the current runtime context (or an empty default)."""
    existing = _current_context.get()
    if existing is not None:
        return existing
    ctx = RuntimeContext()
    ctx.bind()
    return ctx


@contextmanager
def scoped_runtime_context(**kwargs: Any) -> Iterator[RuntimeContext]:
    """Context manager that temporarily merges *kwargs* into the current context."""
    parent = current_context()
    child = parent.with_(**kwargs)
    token = _current_context.set(child)
    try:
        yield child
    finally:
        _current_context.reset(token)
