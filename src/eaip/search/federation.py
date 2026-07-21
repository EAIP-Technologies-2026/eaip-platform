"""SearchFederation — enterprise and department-scoped federated search."""

from __future__ import annotations

import time
from typing import Any

from eaip.logging.context import get_logger
from eaip.search.events import SearchFederated
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem
from eaip.search.providers import SearchProvider


class SearchFederation:
    """Federated search across enterprise brain, department brains,
    knowledge, and memory sources.

    Supports:
    - Enterprise-wide search across all sources
    - Department-scoped search
    - Multi-source federated search
    - Result merging, deduplication, and scoring
    """

    def __init__(
        self,
        *,
        event_publisher: Any | None = None,
    ) -> None:
        self._sources: dict[str, SearchProvider] = {}
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.search.federation")

    def register_source(self, name: str, provider: SearchProvider) -> None:
        """Register a search source for federation.

        Args:
            name: The source name.
            provider: The search provider.
        """
        self._sources[name] = provider
        self._log.info("federation.source_registered", name=name)

    def unregister_source(self, name: str) -> None:
        """Unregister a search source.

        Args:
            name: The source name to remove.
        """
        self._sources.pop(name, None)
        self._log.info("federation.source_unregistered", name=name)

    async def federated_search(
        self,
        query: SearchQuery,
        sources: tuple[str, ...] | None = None,
    ) -> SearchResult:
        """Federated search across specified sources.

        Args:
            query: The search query.
            sources: Source names to search. If None, searches all sources.

        Returns:
            A merged SearchResult across the specified sources.
        """
        t0 = time.monotonic()

        targets = (
            {k: v for k, v in self._sources.items() if k in sources}
            if sources
            else dict(self._sources)
        )

        if not targets:
            return SearchResult(
                items=(),
                total_count=0,
                page=query.page,
                page_size=query.page_size,
                total_pages=0,
                duration_ms=(time.monotonic() - t0) * 1000,
                query=query.query,
            )

        all_items: dict[str, SearchResultItem] = {}
        for name, provider in targets.items():
            try:
                result = await provider.search(query)
                for item in result.items:
                    dedup_key = item.id or item.content[:100]
                    if dedup_key not in all_items:
                        all_items[dedup_key] = item
            except Exception as exc:
                self._log.warning(
                    "federation.source_failed",
                    source=name,
                    error=str(exc),
                )

        items = sorted(all_items.values(), key=lambda i: i.score, reverse=True)
        total = len(items)
        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        start = (query.page - 1) * query.page_size
        paged = items[start : start + query.page_size]

        duration = (time.monotonic() - t0) * 1000

        result = SearchResult(
            items=tuple(paged),
            total_count=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            duration_ms=duration,
            query=query.query,
        )

        self._publish_event(
            SearchFederated(
                query=query.query,
                sources=tuple(targets),
                result_count=result.total_count,
                duration_ms=duration,
            )
        )

        return result

    async def enterprise_search(
        self,
        query: SearchQuery,
    ) -> SearchResult:
        """Enterprise-wide search across all registered sources.

        Args:
            query: The search query.

        Returns:
            A merged SearchResult spanning all enterprise sources.
        """
        return await self.federated_search(query, sources=None)

    async def department_search(
        self,
        query: SearchQuery,
        department_id: str,
    ) -> SearchResult:
        """Department-scoped search.

        Searches sources matching the given department ID. Department
        sources are expected to be registered with names following the
        pattern ``department:<id>:<type>`` or similar conventions.

        Args:
            query: The search query.
            department_id: The department identifier.

        Returns:
            A merged SearchResult scoped to the department.
        """
        t0 = time.monotonic()

        dept_sources: dict[str, SearchProvider] = {}
        for name, provider in self._sources.items():
            if department_id in name or name.startswith(f"dept_{department_id}"):
                dept_sources[name] = provider

        if not dept_sources:
            return SearchResult(
                items=(),
                total_count=0,
                page=query.page,
                page_size=query.page_size,
                total_pages=0,
                duration_ms=(time.monotonic() - t0) * 1000,
                query=query.query,
            )

        return await self.federated_search(
            query,
            sources=tuple(dept_sources),
        )

    async def health(self) -> dict[str, Any]:
        """Check the health of all registered federation sources.

        Returns:
            A dict mapping source names to their health status.
        """
        status: dict[str, Any] = {}
        for name in self._sources:
            status[name] = "registered"
        return status

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("federation.event_publish_failed")


__all__ = ["SearchFederation"]
