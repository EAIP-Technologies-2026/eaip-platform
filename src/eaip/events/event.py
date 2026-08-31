"""Base class for domain events.

Events are immutable :class:`pydantic.BaseModel` instances carrying a stable
``event_type`` (used for routing) and an ``occurred_at`` timestamp. Concrete
events live in their owning packages.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now


class DomainEvent(BaseModel):
    """Base class for all in-process events."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: Subclasses override this to declare their stable event type string.
    event_type: ClassVar[str] = "eaip.event"

    #: Stable event identity — generated once per event instance.  Durable
    #: stores (event store, dead letters) use this to guarantee idempotency.
    id: str = Field(default_factory=lambda: str(uuid4()))

    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: CorrelationId | None = Field(default=None)
    #: Optional tenant scoping. Persisted stores use this to enforce isolation.
    tenant_id: str | None = Field(default=None)


__all__ = ["DomainEvent"]
