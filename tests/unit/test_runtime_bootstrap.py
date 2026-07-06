"""Unit tests for :mod:`eaip.runtime.bootstrap`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import LifecycleError
from eaip.runtime.bootstrap import BootstrapManager
from eaip.runtime.context import RuntimeContext


class _FakeKernel:
    """Minimal kernel stand-in for bootstrap tests."""

    def __init__(self) -> None:
        self.started = False

    @property
    def host(self) -> object:
        return self

    @property
    def registry(self) -> object:
        return self

    @property
    def bootstrap(self) -> object:
        return self


@pytest.mark.asyncio
async def test_pre_start_hooks_run_in_order() -> None:
    bm = BootstrapManager()
    order: list[str] = []

    bm.add_pre_start("first", lambda _k, _ctx: order.append("first"))
    bm.add_pre_start("second", lambda _k, _ctx: order.append("second"))

    kernel = _FakeKernel()
    ctx = RuntimeContext.create()
    await bm.run_pre_start(kernel, ctx)

    assert order == ["first", "second"]


@pytest.mark.asyncio
async def test_post_start_hooks_run_in_order() -> None:
    bm = BootstrapManager()
    order: list[str] = []

    bm.add_post_start("a", lambda _k, _ctx: order.append("a"))
    bm.add_post_start("b", lambda _k, _ctx: order.append("b"))

    kernel = _FakeKernel()
    ctx = RuntimeContext.create()
    await bm.run_post_start(kernel, ctx)

    assert order == ["a", "b"]


@pytest.mark.asyncio
async def test_async_hook_is_awaited() -> None:
    bm = BootstrapManager()
    flag = False

    async def _async_hook(_k: object, _ctx: RuntimeContext) -> None:
        nonlocal flag
        flag = True

    bm.add_pre_start("async", _async_hook)
    await bm.run_pre_start(_FakeKernel(), RuntimeContext.create())
    assert flag


@pytest.mark.asyncio
async def test_sync_hooks_work() -> None:
    bm = BootstrapManager()
    flag = False

    def _sync_hook(_k: object, _ctx: RuntimeContext) -> None:
        nonlocal flag
        flag = True

    bm.add_pre_start("sync", _sync_hook)
    await bm.run_pre_start(_FakeKernel(), RuntimeContext.create())
    assert flag


@pytest.mark.asyncio
async def test_pre_start_failure_raises_lifecycle_error() -> None:
    bm = BootstrapManager()

    def _failing(_k: object, _ctx: RuntimeContext) -> None:
        raise RuntimeError("bootstrap boom")

    bm.add_pre_start("fail", _failing)

    with pytest.raises(LifecycleError, match="pre_start"):
        await bm.run_pre_start(_FakeKernel(), RuntimeContext.create())


@pytest.mark.asyncio
async def test_post_start_failure_raises_lifecycle_error() -> None:
    bm = BootstrapManager()

    def _failing(_k: object, _ctx: RuntimeContext) -> None:
        raise RuntimeError("post boom")

    bm.add_post_start("fail", _failing)

    with pytest.raises(LifecycleError, match="post_start"):
        await bm.run_post_start(_FakeKernel(), RuntimeContext.create())


def test_add_pre_start_empty_name_raises() -> None:
    bm = BootstrapManager()
    with pytest.raises(ValueError, match="non-empty"):
        bm.add_pre_start("", lambda _k, _ctx: None)


def test_add_post_start_empty_name_raises() -> None:
    bm = BootstrapManager()
    with pytest.raises(ValueError, match="non-empty"):
        bm.add_post_start("", lambda _k, _ctx: None)


def test_counts() -> None:
    bm = BootstrapManager()
    assert bm.pre_start_count == 0
    assert bm.post_start_count == 0
    assert bm.hook_count == 0

    bm.add_pre_start("a", lambda _k, _ctx: None)
    assert bm.pre_start_count == 1
    assert bm.hook_count == 1

    bm.add_post_start("b", lambda _k, _ctx: None)
    assert bm.post_start_count == 1
    assert bm.hook_count == 2
