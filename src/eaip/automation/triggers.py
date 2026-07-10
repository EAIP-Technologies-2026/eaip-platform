"""Trigger service - event processing, listener management, schedule checking."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Callable

from eaip.automation.events import RuleTriggered
from eaip.automation.exceptions import TriggerProcessingError
from eaip.automation.models import TriggerEvent, TriggerType
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class TriggerService:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.automation.triggers")
        self._listeners: dict[str, list[Callable[[TriggerEvent], Any]]] = {}
        self._subscriptions: dict[str, Any] = {}

    async def process_event(self, event: TriggerEvent) -> None:
        self._log.info("trigger.event.processed", event_type=event.type, source=event.source)
        listeners = self._listeners.get(event.type, []) + self._listeners.get("*", [])
        for handler in listeners:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as exc:
                self._log.error("trigger.handler.failed", event_type=event.type, error=str(exc))

    async def create_trigger_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "automation",
        correlation_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TriggerEvent:
        event = TriggerEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=datetime.now(),
            payload=payload,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        await self._event_bus.publish(
            RuleTriggered(
                rule_id="",
                rule_name="",
                trigger_type=TriggerType.EVENT,
                trigger_event=event.model_dump(),
            ),
        )
        return event

    def register_event_listener(
        self, event_type: str, handler: Callable[[TriggerEvent], Any],
    ) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        self._log.debug("trigger.listener.registered", event_type=event_type)

    def unregister_event_listener(
        self, event_type: str, handler: Callable[[TriggerEvent], Any],
    ) -> None:
        listeners = self._listeners.get(event_type, [])
        if handler in listeners:
            self._listeners[event_type] = [h for h in listeners if h is not handler]
            self._log.debug("trigger.listener.unregistered", event_type=event_type)

    async def check_scheduled_rules(self) -> list[TriggerEvent]:
        return []


__all__ = ["TriggerService"]
