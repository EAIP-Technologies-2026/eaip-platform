"""RuntimeContext — per-execution ambient context propagated through the runtime.

A :class:`RuntimeContext` is an immutable snapshot of the execution environment
for a single runtime invocation (agent run, job, request, etc.). It is threaded
through every module call via Python's :mod:`contextvars` so that structured
logging, telemetry, and policy evaluation can always access current tracing IDs,
tenant identity, and environment information without explicit parameter passing.

Design constraints
------------------
- **Immutable by default** — context fields are frozen; derivations create new
  contexts via :meth:`derive`.
- **Serialisable** — all fields are plain strings or ``None`` so the context
  can round-trip through JSON or OTel baggage without loss.
- **Propagation via contextvars** — callers use :func:`current_context` and
  :func:`run_with_context`; the context flows automatically across
  ``asyncio.Task`` boundaries.
"""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Any
from uuid import uuid4

from eaip.runtime.exceptions import RuntimeContextError

# ---------------------------------------------------------------------------
# Context variable — module-private; access via helpers below.
# ---------------------------------------------------------------------------
_CTX_VAR: contextvars.ContextVar[RuntimeContext | None] = contextvars.ContextVar(
    "eaip_runtime_context",
    default=None,
)


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Ambient execution context for a single runtime invocation.

    Attributes:
    ----------
    run_id:
        Unique identifier for this execution (agent run, batch job, etc.).
        Auto-generated as a UUID4 hex string when not supplied.
    trace_id:
        Distributed tracing ID propagated from (or to) upstream systems.
        Defaults to a fresh UUID4 hex when not provided.
    span_id:
        Current span within the trace. Assigned by the telemetry layer.
    tenant_id:
        Tenant that owns this execution. ``None`` for single-tenant deployments.
    user_id:
        Identity of the human or service principal that triggered this run.
    environment:
        Deployment environment name (e.g. ``"production"``, ``"local"``).
    parent_run_id:
        ``run_id`` of the calling context when this run was triggered by another
        (nested or sub-agent) invocation.
    tags:
        Arbitrary string key-value pairs for policy / routing decisions.
    """

    run_id: str
    trace_id: str
    span_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    environment: str = "local"
    parent_run_id: str | None = None
    tags: tuple[tuple[str, str], ...] = ()

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        *,
        run_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        environment: str = "local",
        parent_run_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> RuntimeContext:
        """Create a new :class:`RuntimeContext` with sane defaults."""
        return cls(
            run_id=run_id or uuid4().hex,
            trace_id=trace_id or uuid4().hex,
            tenant_id=tenant_id,
            user_id=user_id,
            environment=environment,
            parent_run_id=parent_run_id,
            tags=tuple(sorted((tags or {}).items())),
        )

    def derive(self, **overrides: Any) -> RuntimeContext:
        """Return a new context derived from this one with ``overrides`` applied.

        The ``run_id`` is always freshly generated unless explicitly supplied.
        """
        base = {
            "run_id": uuid4().hex,
            "parent_run_id": self.run_id,
            "trace_id": self.trace_id,
            "environment": self.environment,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "tags": self.tags,
        }
        base.update(overrides)
        return replace(self, **base)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Tag helpers
    # ------------------------------------------------------------------
    def get_tag(self, key: str) -> str | None:
        """Return the value of a tag by key, or ``None`` if not present."""
        for k, v in self.tags:
            if k == key:
                return v
        return None

    def with_tag(self, key: str, value: str) -> RuntimeContext:
        """Return a copy of this context with the tag ``key=value`` merged in."""
        updated = dict(self.tags)
        updated[key] = value
        return replace(self, tags=tuple(sorted(updated.items())))

    def with_span(self, span_id: str) -> RuntimeContext:
        """Return a copy with ``span_id`` updated (used by the telemetry layer)."""
        return replace(self, span_id=span_id)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dict representation."""
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "environment": self.environment,
            "parent_run_id": self.parent_run_id,
            "tags": dict(self.tags),
        }

    def __repr__(self) -> str:
        return (
            f"RuntimeContext(run_id={self.run_id!r}, "
            f"trace_id={self.trace_id!r}, "
            f"tenant_id={self.tenant_id!r}, "
            f"environment={self.environment!r})"
        )


# ---------------------------------------------------------------------------
# Context-var helpers — module-level public API
# ---------------------------------------------------------------------------


def current_context() -> RuntimeContext | None:
    """Return the :class:`RuntimeContext` for the current asyncio task, or ``None``."""
    return _CTX_VAR.get()


def require_context() -> RuntimeContext:
    """Return the current :class:`RuntimeContext`; raise if none is active.

    Use this in code paths that must operate inside a runtime invocation.
    """
    ctx = _CTX_VAR.get()
    if ctx is None:
        raise RuntimeContextError(
            "no RuntimeContext is active in this task; "
            "call run_with_context() or set_context() first"
        )
    return ctx


def set_context(ctx: RuntimeContext) -> contextvars.Token[RuntimeContext | None]:
    """Bind ``ctx`` to the current task.  Returns a token for restoration."""
    return _CTX_VAR.set(ctx)


def reset_context(token: contextvars.Token[RuntimeContext | None]) -> None:
    """Restore the context to its state before the corresponding :func:`set_context`."""
    _CTX_VAR.reset(token)


@contextmanager
def run_with_context(ctx: RuntimeContext) -> Iterator[None]:
    """Temporarily bind *ctx* as the current :class:`RuntimeContext`.

    Use as a context manager to scope a context to a block::

        with run_with_context(ctx):
            assert current_context() is ctx

    The previous context is restored on exit.
    """
    token = set_context(ctx)
    try:
        yield
    finally:
        reset_context(token)


__all__ = [
    "RuntimeContext",
    "current_context",
    "require_context",
    "reset_context",
    "run_with_context",
    "set_context",
]
