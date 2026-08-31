"""ContextBuilder — assemble context from multiple sources with filtering and token management."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.context.events import ContextAssembled
from eaip.context.exceptions import ContextAssemblyError
from eaip.context.models import AssembledContext, ContextBuilderConfig, ContextDocument
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


# Simple token estimate: ~4 characters per token
_TOKEN_FACTOR: float = 4.0


def _estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.

    Args:
        text: The input text.

    Returns:
        An approximate token count.
    """
    return max(1, len(text) // int(_TOKEN_FACTOR))


class ContextBuilder:
    """Assembles context from multiple sources with filtering and token management.

    Integrates with the Memory Engine and Knowledge Engine to gather
    relevant context documents, applies relevance thresholds, truncates
    to a maximum token budget, and supports merging of multiple contexts.
    """

    def __init__(
        self,
        config: ContextBuilderConfig | None = None,
        *,
        memory_engine: Any = None,
        knowledge_engine: Any = None,
        event_publisher: Callable[[object], None] | None = None,
    ) -> None:
        """Initialize the ContextBuilder.

        Args:
            config: Configuration for context assembly.
            memory_engine: Optional Memory Engine instance.
            knowledge_engine: Optional Knowledge Engine instance.
            event_publisher: Optional callable for publishing domain events.
        """
        self._config = config or ContextBuilderConfig()
        self._memory_engine = memory_engine
        self._knowledge_engine = knowledge_engine
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.context.builder")

    @property
    def config(self) -> ContextBuilderConfig:
        """Return the current configuration."""
        return self._config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def assemble(
        self,
        *,
        query: str = "",
        memory_queries: Sequence[str] | None = None,
        knowledge_queries: Sequence[str] | None = None,
        extra_documents: Sequence[ContextDocument] | None = None,
    ) -> AssembledContext:
        """Assemble context from multiple sources.

        Gathers documents from memory and knowledge engines based on
        the provided queries, applies filters, and truncates to the
        configured token budget.

        Args:
            query: Optional primary query string.
            memory_queries: Optional queries for memory retrieval.
            knowledge_queries: Optional queries for knowledge retrieval.
            extra_documents: Optional pre-built documents to include.

        Returns:
            An AssembledContext with filtered and truncated documents.

        Raises:
            ContextAssemblyError: If assembly fails.
        """
        t0 = time.monotonic()
        all_docs: list[ContextDocument] = []

        try:
            if extra_documents:
                all_docs.extend(extra_documents)

            if self._memory_engine and memory_queries:
                mem_docs = await self._retrieve_from_memory(memory_queries)
                all_docs.extend(mem_docs)

            if self._knowledge_engine and knowledge_queries:
                kn_docs = await self._retrieve_from_knowledge(knowledge_queries)
                all_docs.extend(kn_docs)

            if query and not memory_queries and not knowledge_queries:
                if self._memory_engine:
                    mem_docs = await self._retrieve_from_memory([query])
                    all_docs.extend(mem_docs)
                if self._knowledge_engine:
                    kn_docs = await self._retrieve_from_knowledge([query])
                    all_docs.extend(kn_docs)

            result = self._filter_and_truncate(all_docs)
        except Exception as exc:
            raise ContextAssemblyError(f"Failed to assemble context: {exc}") from exc

        duration_ms = (time.monotonic() - t0) * 1000.0
        self._event_publisher(
            ContextAssembled(
                document_count=result.document_count,
                total_tokens=result.total_tokens,
                duration_ms=duration_ms,
            )
        )

        self._log.info(
            "context.assembled",
            documents=result.document_count,
            tokens=result.total_tokens,
            duration_ms=round(duration_ms, 1),
        )
        return result

    def merge(self, contexts: Sequence[AssembledContext]) -> AssembledContext:
        """Merge multiple assembled contexts into one.

        Documents are concatenated in order, deduplicated by source
        if configured, and truncated to the configured token budget.

        Args:
            contexts: The contexts to merge.

        Returns:
            A single merged AssembledContext.
        """
        seen_sources: set[str] = set()
        merged_docs: list[ContextDocument] = []

        for ctx in contexts:
            for doc in ctx.documents:
                if self._config.deduplicate and doc.source:
                    if doc.source in seen_sources:
                        continue
                    seen_sources.add(doc.source)
                merged_docs.append(doc)

        return self._filter_and_truncate(merged_docs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _retrieve_from_memory(self, queries: Sequence[str]) -> list[ContextDocument]:
        """Retrieve context documents from the Memory Engine."""
        docs: list[ContextDocument] = []
        engine = self._memory_engine
        if engine is None:
            return docs

        try:
            for q in queries:
                if hasattr(engine, "search"):
                    results = await engine.search(q)
                    for item in getattr(results, "items", results or []):
                        content = _extract_content(item)
                        if content:
                            docs.append(
                                ContextDocument(
                                    content=content,
                                    source=f"memory:{q}",
                                    relevance_score=getattr(item, "score", 0.0),
                                )
                            )
        except Exception as exc:
            self._log.warning("memory.retrieve.failed", error=str(exc))
        return docs

    async def _retrieve_from_knowledge(self, queries: Sequence[str]) -> list[ContextDocument]:
        """Retrieve context documents from the Knowledge Engine."""
        docs: list[ContextDocument] = []
        engine = self._knowledge_engine
        if engine is None:
            return docs

        try:
            for q in queries:
                if hasattr(engine, "search"):
                    result = await engine.search(q, top_k=self._config.max_documents)
                    for chunk in getattr(result, "chunks", result or []):
                        content = _extract_content(chunk)
                        if content:
                            docs.append(
                                ContextDocument(
                                    content=content,
                                    source=(f"knowledge:{getattr(chunk, 'document_id', '')}"),
                                    relevance_score=getattr(chunk, "score", 0.0),
                                )
                            )
        except Exception as exc:
            self._log.warning("knowledge.retrieve.failed", error=str(exc))
        return docs

    def _filter_and_truncate(self, docs: list[ContextDocument]) -> AssembledContext:
        """Apply relevance threshold, sort by score, and truncate to token budget.

        Args:
            docs: The source documents to filter and truncate.

        Returns:
            A filtered and truncated AssembledContext.
        """
        threshold = self._config.relevance_threshold
        if threshold > 0.0:
            docs = [d for d in docs if d.relevance_score >= threshold]

        docs.sort(key=lambda d: d.relevance_score, reverse=True)

        if self._config.max_documents > 0:
            docs = docs[: self._config.max_documents]

        budget = self._config.max_tokens
        kept: list[ContextDocument] = []
        total = 0

        for doc in docs:
            tokens = _estimate_tokens(doc.content)
            if total + tokens > budget:
                remaining = budget - total
                if remaining > 0:
                    truncated = doc.content[: int(remaining * _TOKEN_FACTOR)]
                    kept.append(
                        ContextDocument(
                            content=truncated,
                            source=doc.source,
                            relevance_score=doc.relevance_score,
                            metadata=doc.metadata,
                        )
                    )
                    total += _estimate_tokens(truncated)
                break
            kept.append(doc)
            total += tokens

        return AssembledContext(
            documents=tuple(kept),
            total_tokens=total,
            document_count=len(kept),
        )


def _extract_content(item: Any) -> str:
    """Extract textual content from a retrieval result item."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("content", item.get("text", "")))
    for attr in ("content", "text", "page_content"):
        candidate = getattr(item, attr, None)
        if isinstance(candidate, str) and candidate:
            return candidate
    return str(item)


__all__ = ["ContextBuilder"]
