"""EnterpriseSearchEngine — federated search across all registered providers."""

from __future__ import annotations

import time
from typing import Any

from eaip.logging.context import get_logger
from eaip.search.events import (
    ProviderRegistered,
    ProviderUnregistered,
    SearchExecuted,
)
from eaip.search.exceptions import (
    ProviderNotFoundError,
    SearchQueryError,
)
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem
from eaip.search.providers import SearchProvider


class EnterpriseSearchEngine:
    """Enterprise search engine that aggregates results across providers.

    Supports:
    - Multiple registered search providers
    - Cross-provider result merging, deduplication, and reranking
    - Provider-specific search
    - Pagination support
    """

    def __init__(
        self,
        *,
        event_publisher: Any | None = None,
    ) -> None:
        self._providers: dict[str, SearchProvider] = {}
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.search.engine")

    @property
    def providers(self) -> dict[str, SearchProvider]:
        return dict(self._providers)

    def register_provider(self, provider: SearchProvider) -> None:
        """Register a search provider.

        Args:
            provider: The search provider to register.

        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        if provider.name in self._providers:
            raise ValueError(f"Provider '{provider.name}' is already registered.")
        self._providers[provider.name] = provider
        self._log.info("engine.provider_registered", name=provider.name)
        self._publish_event(ProviderRegistered(provider_name=provider.name))

    def unregister_provider(self, name: str) -> None:
        """Unregister a search provider.

        Args:
            name: The name of the provider to remove.

        Raises:
            ProviderNotFoundError: If the provider is not registered.
        """
        if name not in self._providers:
            raise ProviderNotFoundError(
                f"Provider '{name}' is not registered.",
                context={"provider_name": name},
            )
        del self._providers[name]
        self._log.info("engine.provider_unregistered", name=name)
        self._publish_event(ProviderUnregistered(provider_name=name))

    async def search(self, query: SearchQuery) -> SearchResult:
        """Execute a search across all registered providers.

        Results from all providers are merged, deduplicated, and
        sorted by score descending.

        Args:
            query: The search query.

        Returns:
            A merged SearchResult with pagination applied.

        Raises:
            SearchQueryError: If the query is invalid.
        """
        t0 = time.monotonic()

        if query.page_size <= 0:
            raise SearchQueryError("page_size must be positive.")

        self._log.info(
            "engine.search",
            query=query.query[:80],
            providers=list(self._providers),
        )

        if not self._providers:
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
        for name, provider in self._providers.items():
            try:
                result = await provider.search(query)
                for item in result.items:
                    dedup_key = item.id or item.content[:100]
                    if dedup_key not in all_items:
                        all_items[dedup_key] = item
                    elif item.score > all_items[dedup_key].score:
                        all_items[dedup_key] = item
            except Exception as exc:
                self._log.warning(
                    "engine.provider_search_failed",
                    provider=name,
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

        self._publish_event(SearchExecuted(
            query=query.query,
            provider_name="enterprise_engine",
            result_count=result.total_count,
            duration_ms=duration,
        ))

        return result

    async def search_provider(
        self,
        provider_name: str,
        query: SearchQuery,
    ) -> SearchResult:
        """Execute a search using a specific registered provider.

        Args:
            provider_name: The name of the provider to use.
            query: The search query.

        Returns:
            A SearchResult from the specified provider.

        Raises:
            ProviderNotFoundError: If the named provider is not registered.
        """
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' not found.",
                context={"provider_name": provider_name},
            )
        return await provider.search(query)

    def get_provider(self, name: str) -> SearchProvider | None:
        """Get a registered provider by name.

        Args:
            name: The provider name.

        Returns:
            The provider if found, None otherwise.
        """
        return self._providers.get(name)

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("engine.event_publish_failed")


__all__ = ["EnterpriseSearchEngine"]
