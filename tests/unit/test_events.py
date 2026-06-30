"""Tests for :mod:`eaip.events`."""

from __future__ import annotations

import asyncio

import pytest

from eaip.events import DomainEvent, EventBus


class _ThingHappened(DomainEvent):
    event_type = "test.thing_happened"
    payload: str


class _SubEvent(_ThingHappened):
    event_type = "test.sub_event"


@pytest.mark.asyncio
async def test_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[str] = []

    async def handler(evt: _ThingHappened) -> None:
        received.append(evt.payload)

    bus.subscribe(_ThingHappened, handler)
    await bus.publish(_ThingHappened(payload="x"))
    assert received == ["x"]


@pytest.mark.asyncio
async def test_sync_handler_supported() -> None:
    bus = EventBus()
    seen: list[str] = []

    def sync_handler(evt: _ThingHappened) -> None:
        seen.append(evt.payload)

    bus.subscribe(_ThingHappened, sync_handler)
    await bus.publish(_ThingHappened(payload="y"))
    assert seen == ["y"]


@pytest.mark.asyncio
async def test_subclass_matching() -> None:
    bus = EventBus()
    count = 0

    async def handler(_evt: _ThingHappened) -> None:
        nonlocal count
        count += 1

    bus.subscribe(_ThingHappened, handler, include_subclasses=True)
    await bus.publish(_SubEvent(payload="x"))
    assert count == 1

    bus2 = EventBus()
    count2 = 0

    async def handler2(_evt: _ThingHappened) -> None:
        nonlocal count2
        count2 += 1

    bus2.subscribe(_ThingHappened, handler2, include_subclasses=False)
    await bus2.publish(_SubEvent(payload="x"))
    assert count2 == 0


@pytest.mark.asyncio
async def test_failing_handler_isolated() -> None:
    bus = EventBus()
    other_called = False

    async def bad(_evt: _ThingHappened) -> None:
        raise RuntimeError("boom")

    async def good(_evt: _ThingHappened) -> None:
        nonlocal other_called
        other_called = True

    bus.subscribe(_ThingHappened, bad)
    bus.subscribe(_ThingHappened, good)
    failures = await bus.publish(_ThingHappened(payload="x"))
    assert other_called
    assert len(failures) == 1
    assert isinstance(failures[0][1], RuntimeError)


@pytest.mark.asyncio
async def test_unsubscribe() -> None:
    bus = EventBus()
    received: list[int] = []

    async def handler(_evt: _ThingHappened) -> None:
        received.append(1)

    sub = bus.subscribe(_ThingHappened, handler)
    assert bus.unsubscribe(sub) is True
    await bus.publish(_ThingHappened(payload="x"))
    assert received == []


def test_subscribe_rejects_non_event_type() -> None:
    bus = EventBus()
    with pytest.raises(TypeError):
        bus.subscribe(str, lambda _e: None)  # type: ignore[arg-type]
