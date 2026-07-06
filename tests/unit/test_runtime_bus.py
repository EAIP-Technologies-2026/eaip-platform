"""Tests for :mod:`eaip.runtime.bus`."""

from __future__ import annotations

import pytest

from eaip.events import DomainEvent, EventBus
from eaip.runtime.bus import RuntimeEventBus
from eaip.runtime.context import RuntimeContext, run_with_context


class _SomethingHappened(DomainEvent):
    event_type = "test.something_happened"
    payload: str = ""


class _OtherEvent(DomainEvent):
    event_type = "test.other_event"


# ---------------------------------------------------------------------------
# Construction & delegation
# ---------------------------------------------------------------------------


def test_wraps_eventbus() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    assert rbus.subscription_count == 0


# ---------------------------------------------------------------------------
# Publishing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_delivers_to_subscribers() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    received: list[str] = []

    async def handler(ev: _SomethingHappened) -> None:
        received.append(ev.payload)

    rbus.subscribe(_SomethingHappened, handler)
    await rbus.publish(_SomethingHappened(payload="hello"))
    assert received == ["hello"]


@pytest.mark.asyncio
async def test_publish_without_context_does_not_set_correlation_id() -> None:
    """When no RuntimeContext is active, correlation_id remains None."""
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    received: list[str | None] = []

    async def handler(ev: _SomethingHappened) -> None:
        received.append(ev.correlation_id)

    rbus.subscribe(_SomethingHappened, handler)
    await rbus.publish(_SomethingHappened(payload="x"))
    assert received == [None]


@pytest.mark.asyncio
async def test_publish_injects_correlation_id_from_context() -> None:
    """When a RuntimeContext is active, correlation_id is set to run_id."""
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    received: list[str | None] = []

    async def handler(ev: _SomethingHappened) -> None:
        received.append(ev.correlation_id)

    rbus.subscribe(_SomethingHappened, handler)
    ctx = RuntimeContext.create()
    with run_with_context(ctx):
        await rbus.publish(_SomethingHappened(payload="x"))

    assert received == [ctx.run_id]


@pytest.mark.asyncio
async def test_publish_does_not_overwrite_existing_correlation_id() -> None:
    """If the event already has a correlation_id, it is preserved."""
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    received: list[str | None] = []

    async def handler(ev: _SomethingHappened) -> None:
        received.append(ev.correlation_id)

    rbus.subscribe(_SomethingHappened, handler)
    ctx = RuntimeContext.create()
    with run_with_context(ctx):
        await rbus.publish(_SomethingHappened(payload="x", correlation_id="existing-id"))

    assert received == ["existing-id"]


@pytest.mark.asyncio
async def test_publish_sync_handler() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    seen: list[str] = []

    def sync_handler(ev: _SomethingHappened) -> None:
        seen.append(ev.payload)

    rbus.subscribe(_SomethingHappened, sync_handler)
    await rbus.publish(_SomethingHappened(payload="sync"))
    assert seen == ["sync"]


# ---------------------------------------------------------------------------
# Subscription management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unsubscribe() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    called = False

    async def handler(_ev: _SomethingHappened) -> None:
        nonlocal called
        called = True

    sub = rbus.subscribe(_SomethingHappened, handler)
    assert rbus.unsubscribe(sub) is True
    await rbus.publish(_SomethingHappened(payload="x"))
    assert not called


@pytest.mark.asyncio
async def test_unsubscribe_unknown_returns_false() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    from eaip.events.bus import Subscription

    fake_sub = Subscription(id="nope", event_type=_SomethingHappened, handler=lambda _: None, include_subclasses=True)
    assert rbus.unsubscribe(fake_sub) is False


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_removes_all_subscriptions() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    called = False

    async def handler(_ev: _SomethingHappened) -> None:
        nonlocal called
        called = True

    rbus.subscribe(_SomethingHappened, handler)
    rbus.clear()
    await rbus.publish(_SomethingHappened(payload="x"))
    assert not called
    assert rbus.subscription_count == 0


# ---------------------------------------------------------------------------
# Subclass matching
# ---------------------------------------------------------------------------


class _MoreSpecificEvent(_SomethingHappened):
    event_type = "test.more_specific"


@pytest.mark.asyncio
async def test_subclass_matching_by_default() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    count = 0

    async def handler(_ev: _SomethingHappened) -> None:
        nonlocal count
        count += 1

    rbus.subscribe(_SomethingHappened, handler)
    await rbus.publish(_MoreSpecificEvent(payload="sub"))
    assert count == 1


# ---------------------------------------------------------------------------
# Rejects non-event type
# ---------------------------------------------------------------------------


def test_subscribe_rejects_non_event() -> None:
    bus = EventBus()
    rbus = RuntimeEventBus(bus)
    with pytest.raises(TypeError):
        rbus.subscribe(str, lambda _e: None)  # type: ignore[arg-type]
