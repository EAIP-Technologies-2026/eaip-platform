"""Unit tests for :mod:`eaip.runtime.context`."""

from __future__ import annotations

import asyncio
import contextvars

import pytest

from eaip.runtime.context import (
    RuntimeContext,
    current_context,
    require_context,
    reset_context,
    run_with_context,
    set_context,
)
from eaip.runtime.exceptions import RuntimeContextError


def test_create_generates_ids() -> None:
    ctx = RuntimeContext.create()
    assert ctx.run_id
    assert ctx.trace_id
    assert ctx.run_id != ctx.trace_id


def test_create_with_explicit_ids() -> None:
    ctx = RuntimeContext.create(run_id="r1", trace_id="t1", environment="prod")
    assert ctx.run_id == "r1"
    assert ctx.trace_id == "t1"
    assert ctx.environment == "prod"


def test_create_with_tags() -> None:
    ctx = RuntimeContext.create(tags={"a": "1", "b": "2"})
    assert ctx.get_tag("a") == "1"
    assert ctx.get_tag("b") == "2"
    assert ctx.get_tag("missing") is None


def test_frozen_context() -> None:
    ctx = RuntimeContext.create()
    with pytest.raises((AttributeError, TypeError)):
        ctx.run_id = "changed"  # type: ignore[misc]


def test_derive_creates_child() -> None:
    parent = RuntimeContext.create(environment="staging", trace_id="t99")
    child = parent.derive()
    assert child.parent_run_id == parent.run_id
    assert child.run_id != parent.run_id
    assert child.trace_id == parent.trace_id  # trace propagates
    assert child.environment == "staging"


def test_derive_with_overrides() -> None:
    parent = RuntimeContext.create()
    child = parent.derive(tenant_id="acme")
    assert child.tenant_id == "acme"


def test_with_tag() -> None:
    ctx = RuntimeContext.create()
    ctx2 = ctx.with_tag("region", "eu-west-1")
    assert ctx2.get_tag("region") == "eu-west-1"
    # Original unchanged
    assert ctx.get_tag("region") is None


def test_with_span() -> None:
    ctx = RuntimeContext.create()
    ctx2 = ctx.with_span("span-001")
    assert ctx2.span_id == "span-001"
    assert ctx.span_id is None


def test_to_dict_has_required_keys() -> None:
    ctx = RuntimeContext.create(run_id="r", trace_id="t", tags={"env": "test"})
    d = ctx.to_dict()
    assert d["run_id"] == "r"
    assert d["trace_id"] == "t"
    assert d["tags"] == {"env": "test"}  # tags included


def test_to_dict_tags_empty_when_no_tags() -> None:
    ctx = RuntimeContext.create()
    d = ctx.to_dict()
    assert d["tags"] == {}


# ---------------------------------------------------------------------------
# run_with_context
# ---------------------------------------------------------------------------


def test_run_with_context_binds_and_restores() -> None:
    ctx = RuntimeContext.create()
    outside = current_context()
    with run_with_context(ctx):
        assert current_context() is ctx
    assert current_context() is outside


def test_run_with_context_restores_on_exception() -> None:
    ctx = RuntimeContext.create()
    outside = current_context()
    try:
        with run_with_context(ctx):
            raise ValueError("boom")
    except ValueError:
        pass
    assert current_context() is outside


# ---------------------------------------------------------------------------
# ContextVar propagation
# ---------------------------------------------------------------------------


def test_set_and_current_context() -> None:
    ctx = RuntimeContext.create()
    token = set_context(ctx)
    assert current_context() is ctx
    reset_context(token)
    assert current_context() is None  # restored


def test_require_context_raises_when_absent() -> None:
    # Run in a fresh context where no RuntimeContext is set.
    def _check() -> None:
        assert current_context() is None
        with pytest.raises(RuntimeContextError):
            require_context()

    # Execute in an isolated contextvars context.
    ctx = contextvars.copy_context()
    ctx.run(_check)


def test_require_context_returns_when_present() -> None:
    runtime_ctx = RuntimeContext.create()
    token = set_context(runtime_ctx)
    try:
        assert require_context() is runtime_ctx
    finally:
        reset_context(token)


@pytest.mark.asyncio
async def test_context_propagates_across_tasks() -> None:
    """RuntimeContext set in parent propagates to child asyncio tasks."""
    runtime_ctx = RuntimeContext.create()
    token = set_context(runtime_ctx)

    results: list[RuntimeContext | None] = []

    async def child() -> None:
        results.append(current_context())

    await asyncio.gather(child())
    assert results[0] is runtime_ctx
    reset_context(token)


def test_repr_contains_key_fields() -> None:
    ctx = RuntimeContext.create(run_id="abc", trace_id="xyz", environment="test")
    r = repr(ctx)
    assert "abc" in r
    assert "xyz" in r
    assert "test" in r
