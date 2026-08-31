"""Event lifecycle hooks — intercept publish and handle lifecycle events."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from eaip.events.envelope import EventEnvelope


class BeforePublishHook(Protocol):
    """Invoked before an event is published to subscribers."""

    async def __call__(self, envelope: EventEnvelope) -> EventEnvelope:
        """Transform or validate the envelope before publish.

        Args:
            envelope: The event envelope about to be published.

        Returns:
            The (possibly modified) envelope. Raise to abort the publish.
        """
        ...


class AfterPublishHook(Protocol):
    """Invoked after all subscribers have processed the event."""

    async def __call__(
        self,
        envelope: EventEnvelope,
        failures: list[tuple[str, BaseException]],
    ) -> None:
        """React to the completed publish.

        Args:
            envelope: The event envelope that was published.
            failures: List of (handler_id, exception) for failed handlers.
        """
        ...


class BeforeHandleHook(Protocol):
    """Invoked before each individual handler invocation."""

    async def __call__(
        self,
        envelope: EventEnvelope,
        handler_id: str,
    ) -> bool:
        """Decide whether to proceed with handler invocation.

        Args:
            envelope: The event envelope being delivered.
            handler_id: An identifier for the handler.

        Returns:
            True to proceed, False to skip this handler.
        """
        ...


class AfterHandleHook(Protocol):
    """Invoked after each handler invocation, regardless of success/failure."""

    async def __call__(
        self,
        envelope: EventEnvelope,
        handler_id: str,
        exception: BaseException | None,
    ) -> None:
        """React to the completed handler invocation.

        Args:
            envelope: The event envelope that was delivered.
            handler_id: An identifier for the handler.
            exception: The exception raised by the handler, or None on success.
        """
        ...


OnErrorCallback = Callable[[EventEnvelope, BaseException, int], Awaitable[None]]


@dataclass
class EventHooks:
    """A collection of lifecycle hooks for event processing.

    All hooks are optional; omitted hooks are simply not called.
    """

    before_publish: BeforePublishHook | None = None
    after_publish: AfterPublishHook | None = None
    before_handle: BeforeHandleHook | None = None
    after_handle: AfterHandleHook | None = None
    on_error: OnErrorCallback | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "AfterHandleHook",
    "AfterPublishHook",
    "BeforeHandleHook",
    "BeforePublishHook",
    "EventHooks",
    "OnErrorCallback",
]
