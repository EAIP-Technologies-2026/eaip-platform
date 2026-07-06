"""Runtime Command Bus — CQRS command dispatch with validation and retry.

The :class:`CommandBus` provides a type-routed command dispatch mechanism:

1. Commands are frozen Pydantic models (like :class:`~eaip.events.event.DomainEvent`).
2. Handlers are registered per command type.
3. Before dispatch, commands pass through a validation pipeline.
4. On failure, configurable retry policies may re-attempt execution.

Usage::

    class PlaceOrder(Command):
        order_id: str
        items: list[str]

    class PlaceOrderHandler:
        async def handle(self, cmd: PlaceOrder) -> None:
            ...

    bus = CommandBus()
    bus.register(PlaceOrder, PlaceOrderHandler())
    await bus.dispatch(PlaceOrder(order_id="123", items=["a", "b"]))
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Protocol, TypeVar, runtime_checkable

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.exceptions.domain import (
    CommandHandlerNotFoundError,
    CommandRetryExhaustedError,
    CommandValidationError,
)
from eaip.logging.context import get_logger
from eaip.shared.time import Duration, utc_now

# ---------------------------------------------------------------------------
# Command message base
# ---------------------------------------------------------------------------


class Command(BaseModel):
    """Base class for all command messages.

    Subclasses declare their payload as Pydantic fields.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    command_type: ClassVar[str] = "eaip.command"
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Handler protocol
# ---------------------------------------------------------------------------


C = TypeVar("C", bound=Command)
R = TypeVar("R")


@runtime_checkable
class CommandHandler(Protocol, Generic[C]):
    """Protocol for command handlers.

    A handler receives a command instance and returns an optional result.
    """

    async def handle(self, command: C) -> Any: ...


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Configuration for command retry behaviour.

    Attributes
    ----------
    max_attempts:
        Maximum number of execution attempts (including the first).
        Defaults to 1 (no retry).
    backoff:
        Base delay between retries.  Each retry doubles the delay.
    max_backoff:
        Maximum delay between retries (cap for exponential backoff).
    retryable_exceptions:
        Tuple of exception types that should trigger a retry.
        Empty tuple means all exceptions are retryable.
    """

    max_attempts: int = 1
    backoff: Duration = Duration.from_milliseconds(100)
    max_backoff: Duration = Duration.from_seconds(10)
    retryable_exceptions: tuple[type[BaseException], ...] = ()

    @property
    def is_enabled(self) -> bool:
        return self.max_attempts > 1


# ---------------------------------------------------------------------------
# Command result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommandResult(Generic[R]):
    """Result of a command dispatch.

    Attributes
    ----------
    success:
        Whether the command completed without error.
    result:
        The handler's return value, if any.
    error:
        The exception that was raised, if any.
    attempts:
        How many attempts were made.
    """
    success: bool
    result: R | None = None
    error: BaseException | None = None
    attempts: int = 1


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


Validator = Callable[[Command], Any]


def default_validator(cmd: Command) -> None:
    """Default validator — raises Pydantic ``ValidationError`` on invalid data.

    Pydantic models are validated at construction time, so this is a pass-
    through for well-typed commands.  Override for custom validation.
    """


# ---------------------------------------------------------------------------
# Command Bus
# ---------------------------------------------------------------------------


class CommandBus:
    """Type-routed command bus with validation and retry.

    Usage::

        bus = CommandBus()
        bus.register(PlaceOrder, PlaceOrderHandler())
        bus.set_validator(my_validator)

        result = await bus.dispatch(PlaceOrder(order_id="123"))

        if result.success:
            ...
        else:
            log.error("command failed", error=result.error)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler[Any]] = {}
        self._handler_retry: dict[str, RetryPolicy] = {}
        self._log = get_logger("eaip.runtime.commands")
        self._validator: Validator = default_validator
        self._default_retry: RetryPolicy = RetryPolicy()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        command_type: type[C],
        handler: CommandHandler[C],
        *,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Register *handler* for *command_type*.

        Args:
            command_type:
                The command class to handle.
            handler:
                An object satisfying the :class:`CommandHandler` protocol.
            retry_policy:
                Optional per-command retry policy.  Falls back to the bus-level
                default if omitted.
        """
        key = self._key(command_type)
        if key in self._handlers:
            self._log.warning(
                "commands.handler_replaced",
                command_type=command_type.__name__,
            )
        self._handlers[key] = handler
        if retry_policy is not None:
            self._handler_retry[key] = retry_policy

    def unregister(self, command_type: type[C]) -> bool:
        """Remove the handler for *command_type*.  Returns ``True`` if present."""
        key = self._key(command_type)
        self._handler_retry.pop(key, None)
        return self._handlers.pop(key, None) is not None

    def has_handler(self, command_type: type[C]) -> bool:
        return self._key(command_type) in self._handlers

    def set_validator(self, validator: Validator) -> None:
        """Set a custom validator called before every dispatch."""
        self._validator = validator

    def set_default_retry(self, policy: RetryPolicy) -> None:
        """Set the default retry policy for all commands."""
        self._default_retry = policy

    def get_handler(self, command_type: type[C]) -> CommandHandler[C] | None:
        key = self._key(command_type)
        handler = self._handlers.get(key)
        return handler

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        command: C,
        *,
        retry_policy: RetryPolicy | None = None,
        raise_on_failure: bool = False,
    ) -> CommandResult[Any]:
        """Dispatch *command* to its registered handler.

        Args:
            command:
                The command instance to dispatch.
            retry_policy:
                Override the default / per-command retry policy.
            raise_on_failure:
                If ``True``, re-raise the underlying exception instead of
                returning a :class:`CommandResult`.

        Returns:
            A :class:`CommandResult` indicating success or failure.

        Raises:
            CommandHandlerNotFoundError:
                If no handler is registered for the command type.
            CommandValidationError:
                If the validator raises.
            CommandRetryExhaustedError:
                If all retry attempts failed and ``raise_on_failure`` is True.
        """
        key = self._key(type(command))
        handler = self._handlers.get(key)
        if handler is None:
            raise CommandHandlerNotFoundError(
                f"no handler registered for {type(command).__name__}",
                context={"command_type": type(command).__name__},
            )

        # Validate.
        try:
            self._validator(command)
        except CommandValidationError:
            raise
        except BaseException as exc:
            raise CommandValidationError(
                f"command {type(command).__name__} validation failed",
                context={"command_type": type(command).__name__},
                cause=exc,
            ) from exc

        # Resolve retry policy.
        policy = retry_policy or self._handler_retry.get(key) or self._default_retry
        attempts = 0
        last_error: BaseException | None = None

        while attempts < policy.max_attempts:
            attempts += 1
            try:
                result = handler.handle(command)
                if inspect.isawaitable(result):
                    result = await result
                return CommandResult(success=True, result=result, attempts=attempts)
            except BaseException as exc:
                last_error = exc
                self._log.warning(
                    "commands.dispatch.failed",
                    command_type=type(command).__name__,
                    attempt=attempts,
                    max_attempts=policy.max_attempts,
                    error=repr(exc),
                )
                if not self._is_retryable(exc, policy):
                    break
                if attempts >= policy.max_attempts:
                    break
                await self._backoff(attempts, policy)

        error = CommandRetryExhaustedError(
            f"command {type(command).__name__} failed after {attempts} attempt(s)",
            context={
                "command_type": type(command).__name__,
                "attempts": attempts,
                "max_attempts": policy.max_attempts,
            },
            cause=last_error,
        )
        if raise_on_failure:
            raise error

        return CommandResult(
            success=False,
            error=last_error,
            attempts=attempts,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _key(command_type: type[Command]) -> str:
        return f"{command_type.__module__}.{command_type.__qualname__}"

    @staticmethod
    def _is_retryable(exc: BaseException, policy: RetryPolicy) -> bool:
        if not policy.retryable_exceptions:
            return True
        return any(isinstance(exc, t) for t in policy.retryable_exceptions)

    @staticmethod
    async def _backoff(attempt: int, policy: RetryPolicy) -> None:
        delay = min(
            policy.backoff.to_timedelta().total_seconds() * (2 ** (attempt - 1)),
            policy.max_backoff.to_timedelta().total_seconds(),
        )
        await asyncio.sleep(delay)


__all__ = [
    "Command",
    "CommandBus",
    "CommandHandler",
    "CommandResult",
    "RetryPolicy",
    "Validator",
    "default_validator",
]
