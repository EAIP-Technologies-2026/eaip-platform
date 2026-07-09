"""Event envelope — wraps a domain event with routing and metadata."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.events.event import DomainEvent


class EventEnvelope(BaseModel):
    """Wraps a :class:`DomainEvent` with delivery metadata.

    The envelope is created when an event is published and tracks
    correlation/causation chains, retry state, and arbitrary metadata
    across handler invocations.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_type: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)
    retry_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_event(
        cls,
        event: DomainEvent,
        *,
        causation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventEnvelope:
        """Create an envelope from a domain event.

        Args:
            event: The domain event to wrap.
            causation_id: Optional id of the event that caused this one.
            metadata: Optional additional metadata.

        Returns:
            A new EventEnvelope.
        """
        event_id = str(CorrelationId.new())
        return cls(
            event_id=event_id,
            event_type=event.event_type,
            payload=event.model_dump(mode="python"),
            correlation_id=str(event.correlation_id) if event.correlation_id else event_id,
            causation_id=causation_id,
            occurred_at=event.occurred_at,
            metadata=metadata or {},
        )


__all__ = ["EventEnvelope"]
