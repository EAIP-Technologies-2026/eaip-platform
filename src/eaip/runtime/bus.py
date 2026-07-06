"""Runtime event bus — context-aware event publishing for the runtime layer.

The :class:`RuntimeEventBus` wraps the platform :class:`~eaip.events.bus.EventBus`
and automatically attaches the current :class:`~eaip.runtime.context.RuntimeContext`
(``run_id`` as ``correlation_id``) to every published event.

Usage inside a runtime host::

    bus = RuntimeEventBus(platform.events)
    await bus.publish(SomeEvent(...))

The :class:`RuntimeHost` exposes this bus via its ``events`` property so that
runtime modules can publish and subscribe to events without reaching directly
into the platform.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from eaip.events.bus import EventBus, Subscription
from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger
from eaip.runtime.context import current_context

if TYPE_CHECKING:  # pragma: no cover
    pass

E = TypeVar("E", bound=DomainEvent)
SyncHandler = Callable[[E], None]
AsyncHandler = Callable[[E], Awaitable[None]]
Handler = SyncHandler[E] | AsyncHandler[E]


class RuntimeEventBus:
    """Context-aware event bus for the runtime layer.

    Delegates subscription management to the underlying platform
    :class:`~eaip.events.bus.EventBus` and injects the current
    :class:`~eaip.runtime.context.RuntimeContext` into each published event's
    ``correlation_id`` field.

    Parameters
    ----------
    bus:
        The platform-level :class:`~eaip.events.bus.EventBus` to delegate to.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._log = get_logger("eaip.runtime.bus")

    # ------------------------------------------------------------------
    # Subscription — delegated to the platform bus
    # ------------------------------------------------------------------

    def subscribe(
        self,
        event_type: type[E],
        handler: Handler[E],
        *,
        include_subclasses: bool = True,
    ) -> Subscription[E]:
        """Register ``handler`` to receive events of ``event_type``.

        Delegates to :meth:`eaip.events.bus.EventBus.subscribe`.
        """
        return self._bus.subscribe(event_type, handler, include_subclasses=include_subclasses)

    def unsubscribe(self, subscription: Subscription[Any]) -> bool:
        """Remove a previously-registered subscription.

        Delegates to :meth:`eaip.events.bus.EventBus.unsubscribe`.
        """
        return self._bus.unsubscribe(subscription)

    # ------------------------------------------------------------------
    # Publishing — context-aware
    # ------------------------------------------------------------------

    async def publish(self, event: DomainEvent) -> list[tuple[Subscription[Any], BaseException]]:
        """Publish ``event``, injecting the current ``RuntimeContext``.

        If a :class:`~eaip.runtime.context.RuntimeContext` is active in the
        current task and the event's ``correlation_id`` is ``None``, the
        context's ``run_id`` is attached automatically.  The event itself is
        **not** mutated (it is frozen); a shallow copy is made if needed.
        """
        ctx = current_context()
        if ctx is not None and event.correlation_id is None:
            event = event.model_copy(update={"correlation_id": ctx.run_id})
        return await self._bus.publish(event)

    # ------------------------------------------------------------------
    # Passthrough helpers
    # ------------------------------------------------------------------

    @property
    def subscription_count(self) -> int:
        """Number of registered subscriptions (delegated to the platform bus)."""
        return self._bus.subscription_count

    def clear(self) -> None:
        """Remove every subscription from the underlying bus."""
        self._bus.clear()


__all__ = [
    "AsyncHandler",
    "Handler",
    "RuntimeEventBus",
    "SyncHandler",
]
