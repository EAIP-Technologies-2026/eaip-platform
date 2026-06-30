"""A small in-process event bus supporting sync & async subscribers.

The bus is **type-routed**: subscribers are bound to a concrete
:class:`DomainEvent` subclass and receive only events of that type (or its
subclasses, when ``include_subclasses=True`` is set).

The bus is **fire-and-collect**: :meth:`publish` awaits every subscriber and
returns the list of (subscriber, exception) tuples for those that raised.
Errors never silently propagate to other subscribers — this is essential for
multi-tenant safety.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import uuid4

from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger

if TYPE_CHECKING:  # pragma: no cover
    pass

E = TypeVar("E", bound=DomainEvent)
SyncHandler = Callable[[E], None]
AsyncHandler = Callable[[E], Awaitable[None]]
Handler = SyncHandler[E] | AsyncHandler[E]


@dataclass(frozen=True, slots=True)
class Subscription(Generic[E]):
    """Opaque handle returned by :meth:`EventBus.subscribe`."""

    id: str
    event_type: type[E]
    handler: Any = field(repr=False)
    include_subclasses: bool


@dataclass(slots=True)
class _Entry:
    sub: Subscription[Any]


class EventBus:
    """Thread-unsafe but task-safe event bus for a single platform instance.

    Designed for in-process pub/sub. Cross-process delivery is out of scope
    for the Foundation; future capabilities may build atop this contract.
    """

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._log = get_logger("eaip.events.bus")

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------
    def subscribe(
        self,
        event_type: type[E],
        handler: Handler[E],
        *,
        include_subclasses: bool = True,
    ) -> Subscription[E]:
        """Register ``handler`` to receive events of ``event_type``."""
        if not isinstance(event_type, type) or not issubclass(event_type, DomainEvent):
            raise TypeError("event_type must be a DomainEvent subclass")
        sub = Subscription(
            id=uuid4().hex,
            event_type=event_type,
            handler=handler,
            include_subclasses=include_subclasses,
        )
        self._entries.append(_Entry(sub=sub))
        self._log.debug(
            "event.subscribed",
            subscription_id=sub.id,
            event_type=event_type.__name__,
            include_subclasses=include_subclasses,
        )
        return sub

    def unsubscribe(self, subscription: Subscription[Any]) -> bool:
        """Remove a previously-registered subscription. Returns True on success."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.sub.id != subscription.id]
        removed = len(self._entries) != before
        if removed:
            self._log.debug("event.unsubscribed", subscription_id=subscription.id)
        return removed

    def clear(self) -> None:
        """Remove every subscription."""
        self._entries.clear()

    @property
    def subscription_count(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    async def publish(self, event: DomainEvent) -> list[tuple[Subscription[Any], BaseException]]:
        """Deliver ``event`` to every matching subscriber.

        Returns a list of ``(subscription, exception)`` for handlers that
        failed. An empty list means every handler succeeded.
        """
        matching = [e for e in self._entries if self._matches(e.sub, event)]
        if not matching:
            return []

        failures: list[tuple[Subscription[Any], BaseException]] = []
        coros: list[Awaitable[None]] = []
        for entry in matching:
            coros.append(self._invoke(entry.sub, event, failures))
        await asyncio.gather(*coros)
        return failures

    async def _invoke(
        self,
        sub: Subscription[Any],
        event: DomainEvent,
        failures: list[tuple[Subscription[Any], BaseException]],
    ) -> None:
        try:
            result = sub.handler(event)
            if inspect.isawaitable(result):
                await result
        except BaseException as exc:  # noqa: BLE001 — bus isolates per subscriber
            failures.append((sub, exc))
            self._log.error(
                "event.handler_failed",
                subscription_id=sub.id,
                event_type=type(event).__name__,
                error=repr(exc),
            )

    @staticmethod
    def _matches(sub: Subscription[Any], event: DomainEvent) -> bool:
        if sub.include_subclasses:
            return isinstance(event, sub.event_type)
        return type(event) is sub.event_type


__all__ = ["AsyncHandler", "EventBus", "Handler", "Subscription", "SyncHandler"]
