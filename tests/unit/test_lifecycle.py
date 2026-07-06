"""Tests for :mod:`eaip.lifecycle`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import LifecycleError
from eaip.lifecycle import LifecycleManager, LifecyclePhase


def test_empty_lifecycle() -> None:
    lm = LifecycleManager()
    assert lm.phase is LifecyclePhase.CREATED
    assert lm.hook_count == 0


@pytest.mark.asyncio
async def test_start_and_stop_order() -> None:
    lm = LifecycleManager()
    events: list[str] = []

    lm.add("a", lambda: events.append("a-start"), lambda: events.append("a-stop"))
    lm.add("b", lambda: events.append("b-start"), lambda: events.append("b-stop"))

    await lm.start()
    assert lm.phase is LifecyclePhase.RUNNING
    await lm.stop()
    assert lm.phase is LifecyclePhase.STOPPED
    assert events == ["a-start", "b-start", "b-stop", "a-stop"]


@pytest.mark.asyncio
async def test_async_hooks_supported() -> None:
    lm = LifecycleManager()
    seen: list[str] = []

    async def a_start() -> None:
        seen.append("a")

    async def a_stop() -> None:
        seen.append("/a")

    lm.add("a", a_start, a_stop)
    await lm.start()
    await lm.stop()
    assert seen == ["a", "/a"]


@pytest.mark.asyncio
async def test_failure_rolls_back() -> None:
    lm = LifecycleManager()
    started: list[str] = []
    stopped: list[str] = []

    lm.add("a", lambda: started.append("a"), lambda: stopped.append("a"))

    def b_start() -> None:
        raise RuntimeError("boom")

    lm.add("b", b_start, lambda: stopped.append("b"))

    with pytest.raises(LifecycleError):
        await lm.start()

    assert lm.phase is LifecyclePhase.FAILED
    assert started == ["a"]
    assert stopped == ["a"]


@pytest.mark.asyncio
async def test_cannot_add_after_start() -> None:
    lm = LifecycleManager()
    await lm.start()
    try:
        with pytest.raises(LifecycleError):
            lm.add("x", lambda: None)
    finally:
        await lm.stop()


@pytest.mark.asyncio
async def test_stop_is_idempotent_for_stopped() -> None:
    lm = LifecycleManager()
    await lm.start()
    await lm.stop()
    await lm.stop()  # no-op
    assert lm.phase is LifecyclePhase.STOPPED


@pytest.mark.asyncio
async def test_stop_from_failed_is_idempotent() -> None:
    """stop() can be called after a failure to reach STOPPED."""
    lm = LifecycleManager()
    lm.add("a", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(LifecycleError):
        await lm.start()
    assert lm.phase is LifecyclePhase.FAILED

    await lm.stop()
    assert lm.phase is LifecyclePhase.STOPPED


@pytest.mark.asyncio
async def test_stop_before_start_is_noop() -> None:
    lm = LifecycleManager()
    await lm.stop()
    assert lm.phase is LifecyclePhase.CREATED


@pytest.mark.asyncio
async def test_empty_start_stop() -> None:
    lm = LifecycleManager()
    await lm.start()
    assert lm.phase is LifecyclePhase.RUNNING
    await lm.stop()
    assert lm.phase is LifecyclePhase.STOPPED


@pytest.mark.asyncio
async def test_hook_count_tracks_registrations() -> None:
    lm = LifecycleManager()
    assert lm.hook_count == 0
    lm.add("a", lambda: None)
    assert lm.hook_count == 1
    lm.add("b", lambda: None, lambda: None)
    assert lm.hook_count == 2
