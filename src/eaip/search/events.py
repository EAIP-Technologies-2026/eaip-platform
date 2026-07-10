"""Search domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class SearchEvent(DomainEvent):
    """Base event for all search events."""

    event_type: ClassVar[str] = "eaip.search.event"


class SearchExecuted(SearchEvent):
    """Published after a search is executed."""

    event_type: ClassVar[str] = "eaip.search.executed"
    query: str
    provider_name: str = ""
    result_count: int = 0
    duration_ms: float = 0.0


class SearchFederated(SearchEvent):
    """Published after a federated search across multiple sources."""

    event_type: ClassVar[str] = "eaip.search.federated"
    query: str
    sources: tuple[str, ...] = ()
    result_count: int = 0
    duration_ms: float = 0.0


class ProviderSearchExecuted(SearchEvent):
    """Published after a search provider executes a search."""

    event_type: ClassVar[str] = "eaip.search.provider.executed"
    provider_name: str
    query: str
    result_count: int = 0
    duration_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = {}


class ProviderRegistered(SearchEvent):
    """Published when a search provider is registered."""

    event_type: ClassVar[str] = "eaip.search.provider.registered"
    provider_name: str


class ProviderUnregistered(SearchEvent):
    """Published when a search provider is unregistered."""

    event_type: ClassVar[str] = "eaip.search.provider.unregistered"
    provider_name: str


__all__ = [
    "ProviderRegistered",
    "ProviderSearchExecuted",
    "ProviderUnregistered",
    "SearchEvent",
    "SearchExecuted",
    "SearchFederated",
]
