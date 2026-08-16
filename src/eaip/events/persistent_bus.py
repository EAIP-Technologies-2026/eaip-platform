"""Persistent event bus — durable, fire-and-collect event delivery.

BATCH 01 (Point 03) wires the existing in-process
:class:`~eaip.events.bus.EventBus` to durable storage.  ``PersistentEventBus``
composes the existing bus with the PostgreSQL-backed event store and dead-letter
queue without changing the bus's public contract.

Delivery ordering (documented in the B01 report's EventBus safety check):

1. **Persist first** — the event is written to the durable event log before any
   subscriber runs.  If persistence fails, the failure is itself captured in a
   dead letter so it is never silently dropped, and subscribers still receive
   the event (best-effort delivery preserves the existing fire-and-collect
   contract).
2. **Dispatch** — subscribers run through the existing fire-and-collect bus;
   every subscriber is invoked and failures are collected, never raised.
3. **Dead-letter failures** — each failed subscription is recorded with the
   original event payload, tenant, handler name, and failure reason.

Deduplication / idempotency: the event's stable ``id`` is the primary key of
both the event log and the dead-letter table, so replaying or re-publishing the
same event instance cannot create duplicate rows.
"""

from __future__ import annotations

from typing import Any

from eaip.events.bus import EventBus, Subscription
from eaip.events.deadletter import DeadLetterQueue
from eaip.events.event import DomainEvent
from eaip.events.store_pg import PgEventStore
from eaip.logging.context import get_logger

log = get_logger("eaip.events.persistent_bus")


class PersistentEventBus:
    """Composes :class:`EventBus` with durable event storage and dead letters."""

    def __init__(
        self,
        bus: EventBus | None = None,
        store: PgEventStore | None = None,
        dead_letter: DeadLetterQueue | None = None,
        *,
        persist: bool = True,
    ) -> None:
        self._bus = bus or EventBus()
        self._store = store or PgEventStore()
        self._dead_letter = dead_letter or DeadLetterQueue()
        self._persist = persist

    # ------------------------------------------------------------------
    # Subscription (delegated to the inner bus)
    # ------------------------------------------------------------------
    def subscribe(self, *args: Any, **kwargs: Any) -> Subscription[Any]:
        return self._bus.subscribe(*args, **kwargs)

    def unsubscribe(self, subscription: Subscription[Any]) -> bool:
        return self._bus.unsubscribe(subscription)

    def clear(self) -> None:
        self._bus.clear()

    @property
    def subscription_count(self) -> int:
        return self._bus.subscription_count

    @property
    def inner(self) -> EventBus:
        return self._bus

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    async def publish(
        self, event: DomainEvent
    ) -> list[tuple[Subscription[Any], BaseException]]:
        if self._persist:
            try:
                await self._store.record(event)
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "persistent_bus.persist_failed",
                    event_id=event.id,
                    event_type=type(event).__name__,
                    error=repr(exc),
                )
                try:
                    await self._dead_letter.record(
                        event,
                        handler_name="persistent_bus.persist",
                        error=exc,
                    )
                except Exception as dl_exc:  # noqa: BLE001
                    log.error(
                        "persistent_bus.deadletter_persist_failed",
                        event_id=event.id,
                        error=repr(dl_exc),
                    )

        failures = await self._bus.publish(event)

        for subscription, exc in failures:
            handler_name = getattr(subscription.handler, "__qualname__", "") or str(
                subscription.handler
            )
            try:
                await self._dead_letter.record(
                    event,
                    handler_name=handler_name,
                    error=exc,
                )
            except Exception as dl_exc:  # noqa: BLE001
                log.error(
                    "persistent_bus.deadletter_failed",
                    event_id=event.id,
                    handler=handler_name,
                    error=repr(dl_exc),
                )

        return failures


__all__ = ["PersistentEventBus"]