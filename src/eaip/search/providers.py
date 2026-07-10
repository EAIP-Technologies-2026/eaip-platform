"""Search providers — protocol and implementations for search backends."""

from __future__ import annotations

import time
from typing import Any, Protocol, runtime_checkable

from eaip.knowledge.federation import KnowledgeFederation
from eaip.knowledge.models import RetrievalResult
from eaip.knowledge.retrieval_engine import RetrievalEngine
from eaip.logging.context import get_logger
from eaip.search.events import ProviderSearchExecuted
from eaip.search.exceptions import ProviderSearchError, SearchQueryError
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for a search provider that can execute searches."""

    name: str

    async def search(self, query: SearchQuery) -> SearchResult:
        """Execute a search and return results.

        Args:
            query: The search query.

        Returns:
            A SearchResult with matched items.
        """
        ...


class KnowledgeSearchProvider:
    """Search provider that wraps RetrievalEngine and KnowledgeFederation.

    Translates SearchQuery into RetrievalEngine/KnowledgeFederation
    calls and maps results to SearchResult.
    """

    def __init__(
        self,
        retrieval_engine: RetrievalEngine | None = None,
        federation: KnowledgeFederation | None = None,
        *,
        event_publisher: Any | None = None,
    ) -> None:
        self._retrieval_engine = retrieval_engine
        self._federation = federation
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.search.providers.knowledge")

    @property
    def name(self) -> str:
        return "knowledge"

    async def search(self, query: SearchQuery) -> SearchResult:
        t0 = time.monotonic()
        self._log.info("knowledge_provider.search", query=query.query[:80])

        try:
            if not query.query.strip():
                raise SearchQueryError("Query text must not be empty.")

            if query.collections:
                if self._federation is not None:
                    raw = await self._federation.search_collections(
                        query.query,
                        query.collections,
                        top_k=query.page_size,
                        score_threshold=query.min_score,
                    )
                elif self._retrieval_engine is not None:
                    raw = await self._search_multi_collections(query)
                else:
                    raise ProviderSearchError(
                        "No retrieval engine or federation available.",
                    )
            else:
                if self._retrieval_engine is not None:
                    raw = await self._retrieval_engine.search(
                        query.query,
                        collection="default",
                        top_k=query.page_size,
                        score_threshold=query.min_score,
                        alpha=query.alpha,
                    )
                elif self._federation is not None:
                    raw = await self._federation.search_enterprise_brain(
                        query.query,
                        top_k=query.page_size,
                    )
                else:
                    raise ProviderSearchError(
                        "No retrieval engine or federation available.",
                    )

            items = self._to_items(raw, query)
            result = self._build_result(items, raw, query, t0)

            self._publish_event(ProviderSearchExecuted(
                provider_name=self.name,
                query=query.query,
                result_count=result.total_count,
                duration_ms=result.duration_ms,
            ))

            return result

        except SearchQueryError:
            raise
        except ProviderSearchError:
            raise
        except Exception as exc:
            raise ProviderSearchError(
                f"Knowledge search failed: {exc}",
                context={"query": query.query[:100]},
                cause=exc,
            ) from exc

    async def _search_multi_collections(self, query: SearchQuery) -> RetrievalResult:
        from eaip.knowledge.models import RetrievalQuery  # noqa: PLC0415

        retrieve = self._retrieval_engine
        if retrieve is None:
            raise ProviderSearchError("RetrievalEngine not available.")
        combined = RetrievalResult(query=query.query, chunks=())
        for coll in query.collections:
            try:
                res = await retrieve.search(
                    query.query,
                    collection=coll,
                    top_k=query.page_size,
                    score_threshold=query.min_score,
                    alpha=query.alpha,
                )
                combined = RetrievalResult(
                    query=combined.query,
                    chunks=combined.chunks + res.chunks,
                    total_results=combined.total_results + res.total_results,
                )
            except Exception as exc:
                self._log.warning(
                    "knowledge_provider.collection_skipped",
                    collection=coll,
                    error=str(exc),
                )
        return combined

    def _to_items(
        self,
        raw: RetrievalResult,
        query: SearchQuery,
    ) -> list[SearchResultItem]:
        items: list[SearchResultItem] = []
        for chunk in raw.chunks:
            attrs = {}
            if chunk.attribution:
                attrs["title"] = chunk.attribution.document_title or ""
                attrs["source"] = chunk.attribution.source or ""
            items.append(SearchResultItem(
                id=chunk.chunk_id,
                collection=chunk.collection,
                content=chunk.content,
                score=chunk.score,
                title=attrs.get("title", ""),
                source=attrs.get("source", ""),
                metadata=dict(chunk.metadata),
            ))
        return items

    def _build_result(
        self,
        items: list[SearchResultItem],
        raw: RetrievalResult,
        query: SearchQuery,
        t0: float,
    ) -> SearchResult:
        total = len(items)
        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        return SearchResult(
            items=tuple(items),
            total_count=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            duration_ms=(time.monotonic() - t0) * 1000,
            query=query.query,
        )

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("knowledge_provider.event_publish_failed")


class MemorySearchProvider:
    """Search provider that wraps a MemoryEngine for memory search."""

    def __init__(
        self,
        memory_search_fn: Any | None = None,
        *,
        event_publisher: Any | None = None,
    ) -> None:
        self._memory_search_fn = memory_search_fn
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.search.providers.memory")

    @property
    def name(self) -> str:
        return "memory"

    async def search(self, query: SearchQuery) -> SearchResult:
        t0 = time.monotonic()
        self._log.info("memory_provider.search", query=query.query[:80])

        try:
            if self._memory_search_fn is None:
                return SearchResult(
                    items=(),
                    total_count=0,
                    page=query.page,
                    page_size=query.page_size,
                    total_pages=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    query=query.query,
                )

            raw = await self._memory_search_fn(query.query, query.page_size)

            items = self._to_items(raw)

            total = len(items)
            total_pages = max(1, (total + query.page_size - 1) // query.page_size)
            result = SearchResult(
                items=tuple(items),
                total_count=total,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
                duration_ms=(time.monotonic() - t0) * 1000,
                query=query.query,
            )

            self._publish_event(ProviderSearchExecuted(
                provider_name=self.name,
                query=query.query,
                result_count=result.total_count,
                duration_ms=result.duration_ms,
            ))

            return result

        except Exception as exc:
            raise ProviderSearchError(
                f"Memory search failed: {exc}",
                context={"query": query.query[:100]},
                cause=exc,
            ) from exc

    def _to_items(self, raw: Any) -> list[SearchResultItem]:
        items: list[SearchResultItem] = []
        try:
            results = raw.results if hasattr(raw, "results") else raw
            for result in results:
                memory = result.memory if hasattr(result, "memory") else result
                content = getattr(memory, "content", str(memory))
                mem_id = getattr(memory, "memory_id", "")
                mem_type = getattr(memory, "memory_type", None)
                mem_type_str = mem_type.value if mem_type is not None else ""
                score = getattr(result, "score", 0.0)
                meta = dict(getattr(memory, "metadata", {}))
                if mem_type_str:
                    meta["memory_type"] = mem_type_str
                items.append(SearchResultItem(
                    id=str(mem_id),
                    collection="memory",
                    content=content,
                    score=float(score),
                    title="",
                    source="memory",
                    metadata=meta,
                ))
        except Exception as exc:
            self._log.warning("memory_provider.to_items_failed", error=str(exc))
        return items

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("memory_provider.event_publish_failed")


class CompositeSearchProvider:
    """Combines multiple search providers, merges and re-orders results."""

    def __init__(
        self,
        providers: list[SearchProvider] | None = None,
    ) -> None:
        self._providers: list[SearchProvider] = providers or []
        self._log = get_logger("eaip.search.providers.composite")

    @property
    def name(self) -> str:
        return "composite"

    @property
    def providers(self) -> list[SearchProvider]:
        return list(self._providers)

    async def search(self, query: SearchQuery) -> SearchResult:
        t0 = time.monotonic()
        self._log.info("composite_provider.search", providers=[p.name for p in self._providers])

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
        for provider in self._providers:
            try:
                result = await provider.search(query)
                for item in result.items:
                    dedup_key = item.id or item.content[:100]
                    if dedup_key not in all_items:
                        all_items[dedup_key] = item
            except Exception as exc:
                self._log.warning(
                    "composite_provider.provider_failed",
                    provider=provider.name,
                    error=str(exc),
                )

        items = sorted(all_items.values(), key=lambda i: i.score, reverse=True)
        total = len(items)

        page = query.page
        page_size = query.page_size
        start = (page - 1) * page_size
        paged = items[start : start + page_size]
        total_pages = max(1, (total + page_size - 1) // page_size)

        return SearchResult(
            items=tuple(paged),
            total_count=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            duration_ms=(time.monotonic() - t0) * 1000,
            query=query.query,
        )

    def add_provider(self, provider: SearchProvider) -> None:
        self._providers.append(provider)

    def remove_provider(self, name: str) -> None:
        self._providers = [p for p in self._providers if p.name != name]


__all__ = [
    "CompositeSearchProvider",
    "KnowledgeSearchProvider",
    "MemorySearchProvider",
    "SearchProvider",
]
