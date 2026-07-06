"""Context binding helpers — thin facade over ``structlog.contextvars``."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import structlog
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    get_contextvars,
    unbind_contextvars,
)

from eaip.logging.config import configure_logging, is_configured


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a logger, configuring defaults on first use."""
    if not is_configured():
        configure_logging()
    return structlog.get_logger(name) if name else structlog.get_logger()


def bind_context(**kv: Any) -> None:
    """Bind key-value pairs to the current context (propagates to children)."""
    bind_contextvars(**kv)


def clear_context() -> None:
    """Clear all bound context vars in the current task."""
    clear_contextvars()


def current_context() -> dict[str, Any]:
    """Return a snapshot of the currently bound context."""
    return dict(get_contextvars())


@contextmanager
def scoped_context(**kv: Any) -> Iterator[None]:
    """Bind ``kv`` for the duration of a ``with`` block, restoring on exit."""
    bind_contextvars(**kv)
    try:
        yield
    finally:
        unbind_contextvars(*kv.keys())


__all__ = [
    "bind_context",
    "clear_context",
    "current_context",
    "get_logger",
    "scoped_context",
]
