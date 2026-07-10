"""ContextCompressor — compress assembled context using configurable strategies."""

from __future__ import annotations

import time
from typing import Any

from eaip.context.events import ContextCompressed
from eaip.context.exceptions import CompressionError
from eaip.context.models import (
    AssembledContext, CompressionConfig, CompressionStrategy, ContextDocument,
)
from eaip.logging.context import get_logger


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token.

    Args:
        text: The input text.

    Returns:
        An approximate token count.
    """
    return max(1, len(text) // 4)


class ContextCompressor:
    """Compresses assembled context using configurable strategies.

    Supports three compression strategies:
    - **extractive**: Keeps the highest-relevance documents.
    - **summarize**: Keeps only the single highest-relevance document.
    - **truncate**: Truncates content to fit within token limits.
    """

    def __init__(
        self,
        config: CompressionConfig | None = None,
        *,
        event_publisher: Any = None,
    ) -> None:
        """Initialize the ContextCompressor.

        Args:
            config: Compression configuration.
            event_publisher: Optional callable for publishing domain events.
        """
        self._config = config or CompressionConfig()
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.context.compression")

    @property
    def config(self) -> CompressionConfig:
        """Return the current compression configuration."""
        return self._config

    async def compress(self, context: AssembledContext) -> AssembledContext:
        """Compress an assembled context.

        Applies the configured compression strategy and returns a new
        compressed AssembledContext. The original context is not modified.

        Args:
            context: The context to compress.

        Returns:
            A compressed AssembledContext.

        Raises:
            CompressionError: If compression fails.
        """
        t0 = time.monotonic()
        original_tokens = context.total_tokens

        try:
            strategy = self._config.strategy

            if strategy == CompressionStrategy.EXTRACTIVE:
                result = self._compress_extractive(context)
            elif strategy == CompressionStrategy.SUMMARIZE:
                result = self._compress_summarize(context)
            elif strategy == CompressionStrategy.TRUNCATE:
                result = self._compress_truncate(context)
            else:
                raise CompressionError(f"Unknown compression strategy: {strategy!r}")
        except Exception as exc:
            raise CompressionError(f"Compression failed: {exc}") from exc

        duration_ms = (time.monotonic() - t0) * 1000.0

        self._event_publisher(
            ContextCompressed(
                original_tokens=original_tokens,
                compressed_tokens=result.total_tokens,
                strategy=self._config.strategy.value,
                ratio=(
                    result.total_tokens / original_tokens
                    if original_tokens > 0
                    else 1.0
                ),
            )
        )

        self._log.info(
            "context.compressed",
            strategy=strategy.value,
            original=original_tokens,
            compressed=result.total_tokens,
            ratio=round(result.total_tokens / original_tokens, 3) if original_tokens else 1.0,
            duration_ms=round(duration_ms, 1),
        )
        return result

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _compress_extractive(self, context: AssembledContext) -> AssembledContext:
        """Keep the most relevant documents up to ratio * total_tokens."""
        docs = list(context.documents)
        docs.sort(key=lambda d: d.relevance_score, reverse=True)

        ratio = self._config.ratio
        max_tok = self._config.max_tokens

        kept: list[ContextDocument] = []
        total = 0
        token_budget = int(context.total_tokens * ratio) if context.total_tokens > 0 else max_tok

        if max_tok > 0 and max_tok < token_budget:
            token_budget = max_tok

        for doc in docs:
            tokens = _estimate_tokens(doc.content)
            if total + tokens > token_budget:
                remaining = token_budget - total
                if remaining > 0:
                    truncated = doc.content[: remaining * 4]
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

    def _compress_summarize(self, context: AssembledContext) -> AssembledContext:
        """Keep only the single most relevant document."""
        if not context.documents:
            return context

        best = max(context.documents, key=lambda d: d.relevance_score)
        tokens = _estimate_tokens(best.content)
        return AssembledContext(
            documents=(best,),
            total_tokens=tokens,
            document_count=1,
        )

    def _compress_truncate(self, context: AssembledContext) -> AssembledContext:
        """Truncate the concatenated content to the token limit."""
        max_tok = self._config.max_tokens
        if max_tok <= 0:
            max_tok = self._config.max_tokens
        if max_tok <= 0:
            return context

        kept: list[ContextDocument] = []
        total = 0

        for doc in context.documents:
            tokens = _estimate_tokens(doc.content)
            if total + tokens > max_tok:
                remaining = max_tok - total
                if remaining > 0:
                    truncated = doc.content[: remaining * 4]
                    kept.append(
                        ContextDocument(
                            content=truncated,
                            source=doc.source,
                            relevance_score=doc.relevance_score,
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


__all__ = ["ContextCompressor"]
