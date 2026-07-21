"""Tracing decorator — wrap async functions in OTel spans."""

from __future__ import annotations

import functools
import inspect
from collections.abc import AsyncGenerator, Callable
from typing import Any, ParamSpec, TypeVar

from opentelemetry.trace import SpanKind, StatusCode

from eaip.tracing.provider import get_tracer as _get_eaip_tracer

P = ParamSpec("P")
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def traced(
    span_name: str | None = None,
    attributes: dict[str, str] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> Callable[[F], F]:
    """Decorator that wraps an async function in an OTel span.

    Args:
        span_name: Override the span name (default: ``function.__qualname__``).
        attributes: Static attributes attached to every span activation.
        kind: The span kind.

    Usage::

        @traced(attributes={"component": "provider"})
        async def my_chat(request: ChatRequest) -> ChatResponse: ...
    """
    attrs = dict(attributes) if attributes else {}

    def decorator(func: F) -> F:
        name = span_name or func.__qualname__

        if _is_async_gen(func):

            @functools.wraps(func)
            async def async_gen_wrapper(*args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
                tracer = _get_eaip_tracer()
                with tracer.start_as_current_span(
                    name, kind=kind, attributes=attrs or None
                ) as span:
                    try:
                        async for item in func(*args, **kwargs):
                            yield item
                    except Exception as exc:
                        span.set_status(StatusCode.ERROR, str(exc))
                        span.record_exception(exc)
                        raise

            return async_gen_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_eaip_tracer()
            with tracer.start_as_current_span(name, kind=kind, attributes=attrs or None) as span:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    span.set_status(StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        return async_wrapper  # type: ignore[return-value]

    return decorator


def _is_async_gen(func: Callable[..., Any]) -> bool:
    return inspect.isasyncgenfunction(func)


__all__ = ["traced"]
