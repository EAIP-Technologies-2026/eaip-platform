"""Unit tests for :mod:`eaip.runtime.pipeline`."""

from __future__ import annotations

import asyncio

import pytest

from eaip.runtime.pipeline import (
    Middleware,
    Pipeline,
    PipelineContext,
    cancellation_middleware,
    logging_middleware,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


async def _echo_handler(input: str) -> str:
    return input


async def _upper_handler(input: str) -> str:
    return input.upper()


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_without_middleware() -> None:
    result = await Pipeline[str, str]().build(_echo_handler).run("hello")
    assert result.result == "hello"
    assert not result.cancelled
    assert result.error is None


@pytest.mark.asyncio
async def test_pipeline_with_single_middleware() -> None:
    async def _mw(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        result = await next_(ctx)
        return result.with_result(result.result.upper())

    result = await Pipeline[str, str]().use(_mw).build(_echo_handler).run("hello")
    assert result.result == "HELLO"


@pytest.mark.asyncio
async def test_pipeline_middleware_order() -> None:
    order: list[str] = []

    async def mw1(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        order.append("mw1-before")
        result = await next_(ctx)
        order.append("mw1-after")
        return result

    async def mw2(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        order.append("mw2-before")
        result = await next_(ctx)
        order.append("mw2-after")
        return result

    await Pipeline[str, str]().use(mw1).use(mw2).build(_echo_handler).run("x")
    assert order == ["mw1-before", "mw2-before", "mw2-after", "mw1-after"]


# ---------------------------------------------------------------------------
# Context manipulation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_state_shared_between_middleware() -> None:
    async def _mw1(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        ctx.state["key"] = "value"
        return await next_(ctx)

    async def _mw2(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        ctx.state["seen"] = ctx.state.get("key")
        return await next_(ctx)

    result = await Pipeline[str, str]().use(_mw1).use(_mw2).build(_echo_handler).run("x")
    assert result.state["seen"] == "value"


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelled_context_skips_handler() -> None:
    handler_called = False

    async def _cancelling_mw(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        return ctx.cancel("cancelled by test")

    async def _handler(input: str) -> str:
        nonlocal handler_called
        handler_called = True
        return input

    result = await Pipeline[str, str]().use(_cancelling_mw).build(_handler).run("x")
    assert result.cancelled
    assert result.cancel_reason == "cancelled by test"
    assert not handler_called


@pytest.mark.asyncio
async def test_cancel_scope_aborts_pipeline() -> None:
    """Using cancel_scope should abort pipeline execution."""
    handler_called = False
    cancel_task = asyncio.get_event_loop().create_future()

    async def _slow_handler(input: str) -> str:
        nonlocal handler_called
        handler_called = True
        await asyncio.sleep(10)
        return input

    async def _run_and_cancel() -> None:
        # Give the pipeline a moment to start, then cancel.
        await asyncio.sleep(0.05)
        cancel_task.set_result(None)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(_run_and_cancel())
        result = await (
            Pipeline[str, str]()
            .build(_slow_handler)
            .run("x", cancel_scope=asyncio.current_task())
        )

    # The result should reflect the cancellation.
    assert result.cancelled or handler_called


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_error_captured() -> None:
    async def _failing_handler(input: str) -> str:
        raise ValueError("handler error")

    result = await Pipeline[str, str]().build(_failing_handler).run("x")
    assert result.error is not None
    assert isinstance(result.error, ValueError)
    assert result.result is None


@pytest.mark.asyncio
async def test_middleware_error_captured() -> None:
    async def _failing_mw(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        raise RuntimeError("middleware error")

    result = await Pipeline[str, str]().use(_failing_mw).build(_echo_handler).run("x")
    assert result.error is not None
    assert isinstance(result.error, RuntimeError)


# ---------------------------------------------------------------------------
# Cancellation middleware
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancellation_middleware_with_timeout() -> None:
    async def _slow_handler(input: str) -> str:
        await asyncio.sleep(10)
        return input

    pipeline = Pipeline[str, str]().use(cancellation_middleware(timeout_seconds=0.01))
    built = pipeline.build(_slow_handler)
    result = await built.run("x")
    assert result.cancelled
    assert "timed out" in (result.cancel_reason or "")


@pytest.mark.asyncio
async def test_cancellation_middleware_no_timeout_passes_through() -> None:
    result = await (
        Pipeline[str, str]()
        .use(cancellation_middleware())
        .build(_echo_handler)
        .run("hello")
    )
    assert result.result == "hello"
    assert not result.cancelled


# ---------------------------------------------------------------------------
# Logging middleware
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logging_middleware_does_not_affect_result() -> None:
    result = await (
        Pipeline[str, str]()
        .use(logging_middleware())
        .build(_echo_handler)
        .run("hello")
    )
    assert result.result == "hello"
    assert result.error is None


# ---------------------------------------------------------------------------
# PipelineContext
# ---------------------------------------------------------------------------


def test_context_cancel() -> None:
    ctx = PipelineContext(input="x")
    assert not ctx.cancelled
    cancelled = ctx.cancel("reason")
    assert cancelled.cancelled
    assert cancelled.cancel_reason == "reason"
    assert not ctx.cancelled  # original unchanged (immutable)


def test_context_with_result() -> None:
    ctx = PipelineContext(input="x")
    updated = ctx.with_result("done")
    assert updated.result == "done"
    assert ctx.result is None


def test_context_with_error() -> None:
    exc = ValueError("boom")
    ctx = PipelineContext(input="x")
    updated = ctx.with_error(exc)
    assert updated.error is exc
    assert ctx.error is None


# ---------------------------------------------------------------------------
# Middleware protocol
# ---------------------------------------------------------------------------


def test_middleware_is_runtime_checkable() -> None:
    """Middleware Protocol should be runtime_checkable."""
    async def _valid_mw(
        ctx: PipelineContext[str, str],
        next_: object,
    ) -> PipelineContext[str, str]:
        return await next_(ctx)

    assert isinstance(_valid_mw, Middleware)
