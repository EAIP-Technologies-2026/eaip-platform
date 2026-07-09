"""Event dispatcher — wraps EventBus with hooks, retry, and observability."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from eaip.events.bus import EventBus, Subscription
from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.events.hooks import EventHooks
from eaip.events.retry import ExponentialBackoffRetry, RetryStrategy
from eaip.logging.context import get_logger, scoped_context

if TYPE_CHECKING:
    from eaip.metrics.metrics import Meter


@dataclass
class DispatchResult:
    """The result of publishing an event through the dispatcher."""

    envelope: EventEnvelope
    handler_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    failures: list[tuple[str, BaseException]] = field(default_factory=list)
    retry_attempts: int = 0


HandlerIdFn = Callable[[Any], str]


def _default_handler_id(handler: Any) -> str:
    return f"{type(handler).__module__}.{type(handler).__qualname__}"


class EventDispatcher:
    """Wraps an :class:`EventBus` with lifecycle hooks, retry, and observability.

    The dispatcher is the recommended way to publish events. It:
    - Wraps each event in an :class:`EventEnvelope`.
    - Invokes pre/post publish lifecycle hooks.
    - Retries failed handlers according to a :class:`RetryStrategy`.
    - Emits metrics via a :class:`Meter` when provided.
    - Logs structured events at each lifecycle stage.
    """

    def __init__(
        self,
        bus: EventBus,
        *,
        hooks: EventHooks | None = None,
        retry: RetryStrategy | None = None,
        meter: Meter | None = None,
        handler_id_fn: HandlerIdFn = _default_handler_id,
    ) -> None:
        """Initialise the dispatcher.

        Args:
            bus: The underlying event bus.
            hooks: Optional lifecycle hooks.
            retry: Optional retry strategy (default: ExponentialBackoffRetry).
            meter: Optional meter for metrics.
            handler_id_fn: Function to derive a handler identifier.
        """
        self._bus = bus
        self._hooks = hooks or EventHooks()
        self._retry = retry or ExponentialBackoffRetry()
        self._meter = meter
        self._handler_id_fn = handler_id_fn
        self._log = get_logger("eaip.events.dispatcher")

    @property
    def bus(self) -> EventBus:
        """Return the underlying event bus."""
        return self._bus

    @property
    def hooks(self) -> EventHooks:
        """Return the configured lifecycle hooks."""
        return self._hooks

    @property
    def retry(self) -> RetryStrategy:
        """Return the configured retry strategy."""
        return self._retry

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    async def publish(
        self,
        event: DomainEvent,
        *,
        causation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """Publish a domain event through the dispatcher.

        Creates an envelope, runs lifecycle hooks, delivers to matching
        subscribers with retry, and collects results.

        Args:
            event: The domain event to publish.
            causation_id: Optional causation id linking to a prior event.
            metadata: Optional additional envelope metadata.

        Returns:
            A DispatchResult with delivery outcomes.
        """
        envelope = EventEnvelope.from_event(
            event,
            causation_id=causation_id,
            metadata=metadata,
        )

        with scoped_context(
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            correlation_id=envelope.correlation_id,
        ):
            return await self._do_publish(event, envelope)

    async def _do_publish(self, event: DomainEvent, envelope: EventEnvelope) -> DispatchResult:
        self._log.info("event.publish.start", envelope=envelope.event_id)

        tracer = trace.get_tracer("eaip.events")
        with tracer.start_as_current_span(
            "event.publish",
            kind=SpanKind.INTERNAL,
            attributes={
                "event.type": envelope.event_type,
                "event.id": envelope.event_id,
                "correlation_id": envelope.correlation_id or "",
            },
        ) as span:
            # Pre-publish hook
            if self._hooks.before_publish is not None:
                envelope = await self._hooks.before_publish(envelope)

            # Collect matching subscriptions from the bus.
            subscriptions = [
                entry.sub
                for entry in self._bus._entries
                if self._bus._matches(entry.sub, event)
            ]

            if not subscriptions:
                self._log.info("event.publish.no_subscribers")
                return DispatchResult(envelope=envelope)

            result = DispatchResult(envelope=envelope, handler_count=len(subscriptions))

            # Deliver to each matching subscriber.
            for sub in subscriptions:
                handler_id = self._handler_id_fn(sub.handler)
                success = await self._deliver_with_retry(event, envelope, sub, handler_id, result)
                if success:
                    result.success_count += 1
                else:
                    result.failure_count += 1

            span.set_attribute("event.handler_count", result.handler_count)
            span.set_attribute("event.success_count", result.success_count)
            span.set_attribute("event.failure_count", result.failure_count)
            if result.failure_count > 0:
                span.set_status(StatusCode.ERROR, f"{result.failure_count} handler(s) failed")

            # Post-publish hook
            hooks = self._hooks
            if hooks.after_publish is not None:
                await hooks.after_publish(envelope, result.failures)

            # Metrics
            if self._meter is not None:
                meter = self._meter
                meter.counter("event.published", labels={"event_type": envelope.event_type}).inc()
                if result.failure_count > 0:
                    meter.counter(
                        "event.publish_failures", labels={"event_type": envelope.event_type}
                    ).inc(result.failure_count)
                meter.histogram(
                    "event.handler_count", labels={"event_type": envelope.event_type}
                ).observe(float(result.handler_count))

            self._log.info(
                "event.publish.complete",
                envelope=envelope.event_id,
                handlers=result.handler_count,
                successes=result.success_count,
                failures=result.failure_count,
                retries=result.retry_attempts,
            )
            return result

    async def _deliver_with_retry(
        self,
        event: DomainEvent,
        envelope: EventEnvelope,
        sub: Subscription[Any],
        handler_id: str,
        result: DispatchResult,
    ) -> bool:
        attempt = 0
        while True:
            exception = await self._invoke_handler(event, envelope, sub, handler_id, attempt)
            if exception is None:
                return True

            result.failures.append((sub.id, exception))

            # On-error hook
            if self._hooks.on_error is not None:
                await self._hooks.on_error(envelope, exception, attempt)

            delay = await self._retry.should_retry(envelope, exception, attempt)
            if delay is None:
                self._log.error(
                    "event.handler.retry_exhausted",
                    handler_id=handler_id,
                    subscription_id=sub.id,
                    event_type=envelope.event_type,
                    attempts=attempt,
                )
                return False

            result.retry_attempts += 1
            self._log.info(
                "event.handler.retry",
                handler_id=handler_id,
                attempt=attempt,
                delay=delay,
            )

            if delay > 0:
                await asyncio.sleep(delay)

            envelope = envelope.model_copy(update={"retry_count": attempt + 1})
            attempt += 1

    async def _invoke_handler(
        self,
        event: DomainEvent,
        envelope: EventEnvelope,
        sub: Subscription[Any],
        handler_id: str,
        attempt: int,
    ) -> BaseException | None:
        # Before-handle hook
        if self._hooks.before_handle is not None:
            proceed = await self._hooks.before_handle(envelope, handler_id)
            if not proceed:
                return None

        with scoped_context(handler_id=handler_id, attempt=attempt):
            try:
                result = sub.handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except BaseException as exc:
                # After-handle hook (failure)
                if self._hooks.after_handle is not None:
                    await self._hooks.after_handle(envelope, handler_id, exc)
                return exc

        # After-handle hook (success)
        if self._hooks.after_handle is not None:
            await self._hooks.after_handle(envelope, handler_id, None)
        return None

    # ------------------------------------------------------------------
    # Subscription delegation
    # ------------------------------------------------------------------

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Any,
        *,
        include_subclasses: bool = True,
    ) -> Subscription[Any]:
        """Register a handler on the underlying bus."""
        return self._bus.subscribe(event_type, handler, include_subclasses=include_subclasses)

    def unsubscribe(self, subscription: Subscription[Any]) -> bool:
        """Remove a subscription from the underlying bus."""
        return self._bus.unsubscribe(subscription)

    @property
    def subscription_count(self) -> int:
        """Return the number of subscriptions on the underlying bus."""
        return self._bus.subscription_count


__all__ = ["DispatchResult", "EventDispatcher", "HandlerIdFn"]
