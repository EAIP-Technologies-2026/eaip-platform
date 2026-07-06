"""Runtime Pipeline — middleware chain with execution context and cancellation.

The :class:`Pipeline` provides a composable middleware chain through which
runtime operations flow.  Each middleware wraps the next, enabling cross-cutting
concerns (logging, metrics, auth, retry) to be inserted declaratively.

Key concepts
------------
* **PipelineContext** — immutable snapshot of the execution environment
  (input, state, cancellation, result).
* **Middleware** — a callable that receives ``(ctx, next_)`` and may inspect /
  mutate the context before (and after) calling ``next_``.
* **Pipeline** — composes middleware into an ordered chain and provides a
  ``run`` entry point.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, runtime_checkable

from eaip.exceptions.domain import PipelineError
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from datetime import datetime

T = TypeVar("T", covariant=True)
T_in = TypeVar("T_in", contravariant=True)
T_out = TypeVar("T_out", covariant=True)

# ---------------------------------------------------------------------------
# Execution context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PipelineContext(Generic[T_in, T_out]):
    """Immutable execution context flowing through the middleware chain.

    Attributes
    ----------
    input:
        The initial input to the pipeline.
    state:
        Mutable dictionary that middleware can use to share ephemeral data.
    cancelled:
        ``True`` if a middleware requested cancellation.
    cancel_reason:
        Human-readable reason for cancellation, if any.
    result:
        The final result produced by the terminal handler, once set.
    error:
        The exception raised during execution, if any.
    started_at:
        Timestamp when execution began.
    """

    input: T_in
    state: dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    cancel_reason: str | None = None
    result: T_out | None = None
    error: BaseException | None = None
    started_at: datetime | None = None

    def cancel(self, reason: str = "cancelled") -> PipelineContext[T_in, T_out]:
        """Return a new context marked as cancelled."""
        return PipelineContext(
            input=self.input,
            state=self.state,
            cancelled=True,
            cancel_reason=reason,
            result=self.result,
            error=self.error,
            started_at=self.started_at,
        )

    def with_result(self, value: T_out) -> PipelineContext[T_in, T_out]:
        """Return a new context with the result set."""
        return PipelineContext(
            input=self.input,
            state=self.state,
            cancelled=self.cancelled,
            cancel_reason=self.cancel_reason,
            result=value,
            error=self.error,
            started_at=self.started_at,
        )

    def with_error(self, exc: BaseException) -> PipelineContext[T_in, T_out]:
        """Return a new context with the error set."""
        return PipelineContext(
            input=self.input,
            state=self.state,
            cancelled=self.cancelled,
            cancel_reason=self.cancel_reason,
            result=self.result,
            error=exc,
            started_at=self.started_at,
        )


# ---------------------------------------------------------------------------
# Middleware protocol
# ---------------------------------------------------------------------------


NextCall = Callable[[PipelineContext[T_in, T_out]], Awaitable[PipelineContext[T_in, T_out]]]


@runtime_checkable
class Middleware(Protocol, Generic[T_in, T_out]):
    """Protocol for pipeline middleware.

    A middleware receives the current context and a ``next_`` callable.
    It may inspect, log, or modify the context, then optionally call
    ``next_(ctx)`` to pass control to the next middleware in the chain.
    """

    async def __call__(
        self,
        ctx: PipelineContext[T_in, T_out],
        next_: NextCall[T_in, T_out],
    ) -> PipelineContext[T_in, T_out]: ...


Handler = Callable[[T_in], Awaitable[T_out]]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class Pipeline(Generic[T_in, T_out]):
    """Composable middleware chain.

    Usage::

        pipeline = (
            Pipeline[str, str]()
            .use(logging_middleware)
            .use(auth_middleware)
            .build(handler)
        )
        result_ctx = await pipeline.run("hello")
    """

    def __init__(self) -> None:
        self._middleware: list[Middleware[T_in, T_out]] = []
        self._log = get_logger("eaip.runtime.pipeline")

    def use(self, mw: Middleware[T_in, T_out]) -> Pipeline[T_in, T_out]:
        """Append *mw* to the middleware chain."""
        self._middleware.append(mw)
        return self

    def build(self, handler: Handler[T_in, T_out]) -> _BuiltPipeline[T_in, T_out]:
        """Compile the middleware chain and wrap *handler* as the terminal.

        Returns a :class:`_BuiltPipeline` that can be executed via ``run``.
        """
        chain = self._compose(handler)
        return _BuiltPipeline(chain=chain, log=self._log)

    def _compose(
        self, handler: Handler[T_in, T_out]
    ) -> NextCall[T_in, T_out]:
        chain: NextCall[T_in, T_out] = _terminal(handler)
        for mw in reversed(self._middleware):
            chain = _wrap(mw, chain)
        return chain


class _BuiltPipeline(Generic[T_in, T_out]):
    """A compiled, ready-to-execute pipeline."""

    def __init__(
        self,
        *,
        chain: NextCall[T_in, T_out],
        log: Any,
    ) -> None:
        self._chain = chain
        self._log = log

    async def run(
        self,
        input: T_in,
        *,
        cancel_scope: asyncio.Task[Any] | None = None,
    ) -> PipelineContext[T_in, T_out]:
        """Execute the pipeline with *input*.

        Args:
            input:
                The input value for the pipeline.
            cancel_scope:
                An optional asyncio task whose cancellation will abort the
                pipeline execution.

        Returns:
            The final :class:`PipelineContext` after the middleware chain
            and terminal handler have completed.
        """
        ctx = PipelineContext[T_in, T_out](
            input=input,
            started_at=utc_now(),
        )

        async def _run() -> PipelineContext[T_in, T_out]:
            try:
                result_ctx = await self._chain(ctx)
                return result_ctx
            except asyncio.CancelledError:
                return ctx.cancel("pipeline cancelled via cancel_scope")
            except PipelineError:
                raise
            except BaseException as exc:
                self._log.error(
                    "pipeline.execution_failed",
                    error=repr(exc),
                )
                return ctx.with_error(exc)

        if cancel_scope is not None:
            task = asyncio.ensure_future(_run())
            cancel_scope.add_done_callback(lambda _t: task.cancel() if not task.done() else None)
            return await task

        return await _run()


# ---------------------------------------------------------------------------
# Internal composition helpers
# --------------------------------------------------------------------------


def _terminal(handler: Handler[T_in, T_out]) -> NextCall[T_in, T_out]:
    async def _terminal_fn(ctx: PipelineContext[T_in, T_out]) -> PipelineContext[T_in, T_out]:
        if ctx.cancelled:
            return ctx
        try:
            result = await handler(ctx.input)
            return ctx.with_result(result)
        except Exception as exc:
            return ctx.with_error(exc)

    return _terminal_fn


def _wrap(
    mw: Middleware[T_in, T_out],
    next_: NextCall[T_in, T_out],
) -> NextCall[T_in, T_out]:
    async def _wrapped(ctx: PipelineContext[T_in, T_out]) -> PipelineContext[T_in, T_out]:
        if ctx.cancelled:
            return ctx
        try:
            return await mw(ctx, next_)
        except PipelineError:
            raise
        except Exception as exc:
            return ctx.with_error(exc)

    return _wrapped


# ---------------------------------------------------------------------------
# Built-in middleware factories
# ---------------------------------------------------------------------------


def logging_middleware(
    logger_name: str = "eaip.runtime.pipeline",
) -> Middleware[Any, Any]:
    """Return a middleware that logs pipeline execution start and end."""
    log = get_logger(logger_name)

    async def _mw(
        ctx: PipelineContext[Any, Any],
        next_: NextCall[Any, Any],
    ) -> PipelineContext[Any, Any]:
        log.info("pipeline.middleware.starting", input=repr(ctx.input)[:200])
        result = await next_(ctx)
        if result.error:
            log.error("pipeline.middleware.failed", error=repr(result.error))
        else:
            log.info("pipeline.middleware.completed")
        return result

    return _mw


def cancellation_middleware(
    timeout_seconds: float | None = None,
) -> Middleware[Any, Any]:
    """Return a middleware that enforces an optional timeout.

    If *timeout_seconds* is set, the middleware raises ``asyncio.TimeoutError``
    which is caught by the pipeline and converted to a cancellation.
    """
    async def _mw(
        ctx: PipelineContext[Any, Any],
        next_: NextCall[Any, Any],
    ) -> PipelineContext[Any, Any]:
        if timeout_seconds is None:
            return await next_(ctx)
        try:
            return await asyncio.wait_for(next_(ctx), timeout=timeout_seconds)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return ctx.cancel(f"pipeline timed out after {timeout_seconds}s")

    return _mw


__all__ = [
    "Handler",
    "Middleware",
    "NextCall",
    "Pipeline",
    "PipelineContext",
    "_BuiltPipeline",
    "cancellation_middleware",
    "logging_middleware",
]
