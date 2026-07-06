"""Unit tests for :mod:`eaip.runtime.commands`."""

from __future__ import annotations

import pytest

from pydantic_core import ValidationError

from eaip.exceptions.domain import (
    CommandHandlerNotFoundError,
    CommandRetryExhaustedError,
    CommandValidationError,
)
from typing import ClassVar

from eaip.runtime.commands import Command, CommandBus, CommandHandler, CommandResult, RetryPolicy
from eaip.shared.time import Duration


# ---------------------------------------------------------------------------
# Test command types
# ---------------------------------------------------------------------------


class PlaceOrder(Command):
    command_type: ClassVar[str] = "test.place_order"
    order_id: str = ""


class ShipOrder(Command):
    command_type: ClassVar[str] = "test.ship_order"
    order_id: str = ""


# ---------------------------------------------------------------------------
# Test handlers
# ---------------------------------------------------------------------------


class PlaceOrderHandler:
    def __init__(self) -> None:
        self.received: list[PlaceOrder] = []

    async def handle(self, cmd: PlaceOrder) -> str:
        self.received.append(cmd)
        return f"placed:{cmd.order_id}"


class FailingHandler:
    def __init__(self, fail_count: int = 0) -> None:
        self.attempts = 0
        self._fail_count = fail_count

    async def handle(self, cmd: Command) -> str:
        self.attempts += 1
        if self._fail_count == 0 or self.attempts <= self._fail_count:
            raise RuntimeError(f"attempt {self.attempts} failed")
        return "ok"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_create_command_bus() -> None:
    bus = CommandBus()
    assert bus is not None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_handler() -> None:
    bus = CommandBus()
    handler = PlaceOrderHandler()
    bus.register(PlaceOrder, handler)
    assert bus.has_handler(PlaceOrder)
    assert bus.get_handler(PlaceOrder) is handler


def test_unregister_handler() -> None:
    bus = CommandBus()
    bus.register(PlaceOrder, PlaceOrderHandler())
    assert bus.unregister(PlaceOrder) is True
    assert not bus.has_handler(PlaceOrder)


def test_unregister_unknown_returns_false() -> None:
    bus = CommandBus()
    assert bus.unregister(PlaceOrder) is False


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_success() -> None:
    bus = CommandBus()
    handler = PlaceOrderHandler()
    bus.register(PlaceOrder, handler)

    result = await bus.dispatch(PlaceOrder(order_id="abc"))
    assert result.success
    assert result.result == "placed:abc"
    assert len(handler.received) == 1


@pytest.mark.asyncio
async def test_dispatch_no_handler_raises() -> None:
    bus = CommandBus()
    with pytest.raises(CommandHandlerNotFoundError):
        await bus.dispatch(PlaceOrder(order_id="abc"))


@pytest.mark.asyncio
async def test_dispatch_handler_error() -> None:
    bus = CommandBus()
    bus.register(ShipOrder, FailingHandler())

    result = await bus.dispatch(ShipOrder(order_id="abc"))
    assert not result.success
    assert result.error is not None
    assert isinstance(result.error, RuntimeError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validator_called() -> None:
    bus = CommandBus()
    bus.register(PlaceOrder, PlaceOrderHandler())
    validated: list[object] = []

    def my_validator(cmd: object) -> None:
        validated.append(cmd)

    bus.set_validator(my_validator)
    await bus.dispatch(PlaceOrder(order_id="abc"))
    assert len(validated) == 1


@pytest.mark.asyncio
async def test_validator_raises_command_validation_error() -> None:
    bus = CommandBus()
    bus.register(PlaceOrder, PlaceOrderHandler())

    def failing_validator(cmd: object) -> None:
        raise ValueError("invalid")

    bus.set_validator(failing_validator)
    with pytest.raises(CommandValidationError):
        await bus.dispatch(PlaceOrder(order_id="abc"))


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_on_failure() -> None:
    bus = CommandBus()
    handler = FailingHandler(fail_count=2)
    bus.register(
        PlaceOrder,
        handler,
        retry_policy=RetryPolicy(
            max_attempts=3,
            backoff=Duration.from_milliseconds(10),
        ),
    )

    result = await bus.dispatch(PlaceOrder(order_id="abc"))
    assert result.success
    assert result.attempts == 3


@pytest.mark.asyncio
async def test_retry_exhausted_returns_error() -> None:
    bus = CommandBus()
    handler = FailingHandler(fail_count=99)
    bus.register(
        PlaceOrder,
        handler,
        retry_policy=RetryPolicy(
            max_attempts=3,
            backoff=Duration.from_milliseconds(10),
        ),
    )

    result = await bus.dispatch(PlaceOrder(order_id="abc"))
    assert not result.success
    assert result.attempts == 3


@pytest.mark.asyncio
async def test_retry_exhausted_raises_when_requested() -> None:
    bus = CommandBus()
    handler = FailingHandler(fail_count=99)
    bus.register(
        PlaceOrder,
        handler,
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff=Duration.from_milliseconds(10),
        ),
    )

    with pytest.raises(CommandRetryExhaustedError):
        await bus.dispatch(PlaceOrder(order_id="abc"), raise_on_failure=True)


@pytest.mark.asyncio
async def test_no_retry_by_default() -> None:
    bus = CommandBus()
    handler = FailingHandler(fail_count=1)
    bus.register(PlaceOrder, handler)

    result = await bus.dispatch(PlaceOrder(order_id="abc"))
    assert not result.success
    assert result.attempts == 1


# ---------------------------------------------------------------------------
# Command model
# ---------------------------------------------------------------------------


def test_command_is_frozen() -> None:
    cmd = PlaceOrder(order_id="123")
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        cmd.order_id = "changed"  # type: ignore[misc]


def test_command_extra_fields_forbidden() -> None:
    with pytest.raises((ValueError, TypeError, ValidationError)):
        PlaceOrder(order_id="123", extra="x")  # type: ignore[call-arg]


def test_command_has_occurred_at() -> None:
    cmd = PlaceOrder(order_id="123")
    assert cmd.occurred_at is not None


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------


def test_retry_policy_disabled_by_default() -> None:
    policy = RetryPolicy()
    assert not policy.is_enabled


def test_retry_policy_enabled() -> None:
    policy = RetryPolicy(max_attempts=3)
    assert policy.is_enabled


def test_retry_policy_defaults() -> None:
    policy = RetryPolicy()
    assert policy.max_attempts == 1
    assert policy.backoff == Duration.from_milliseconds(100)
    assert policy.max_backoff == Duration.from_seconds(10)
