"""Tests for ContextCompressor."""

from __future__ import annotations

from eaip.context.compression import ContextCompressor
from eaip.context.models import AssembledContext, CompressionConfig, CompressionStrategy, ContextDocument


class _Helpers:
    @staticmethod
    def make_context(docs: list[tuple[str, float]]) -> AssembledContext:
        total = 0
        documents: list[ContextDocument] = []
        for content, score in docs:
            tokens = max(1, len(content) // 4)
            total += tokens
            documents.append(
                ContextDocument(content=content, relevance_score=score)
            )
        return AssembledContext(
            documents=tuple(documents),
            total_tokens=total,
            document_count=len(documents),
        )


class TestContextCompressor:
    async def test_extractive_keeps_high_score(self) -> None:
        ctx = _Helpers.make_context([
            ("a" * 40, 0.9),
            ("b" * 40, 0.1),
        ])
        compressor = ContextCompressor(CompressionConfig(
            strategy=CompressionStrategy.EXTRACTIVE,
            ratio=0.5,
        ))
        result = await compressor.compress(ctx)
        assert result.document_count >= 1
        assert result.documents[0].relevance_score == 0.9

    async def test_extractive_with_ratio(self) -> None:
        ctx = _Helpers.make_context([
            ("x" * 100, 0.9),
            ("y" * 100, 0.5),
        ])
        compressor = ContextCompressor(CompressionConfig(
            strategy=CompressionStrategy.EXTRACTIVE,
            ratio=0.3,
        ))
        result = await compressor.compress(ctx)
        assert result.total_tokens <= ctx.total_tokens

    async def test_summarize_keeps_best(self) -> None:
        ctx = _Helpers.make_context([
            ("low", 0.1),
            ("medium", 0.5),
            ("high", 0.95),
        ])
        compressor = ContextCompressor(CompressionConfig(
            strategy=CompressionStrategy.SUMMARIZE,
        ))
        result = await compressor.compress(ctx)
        assert result.document_count == 1
        assert result.documents[0].relevance_score == 0.95

    async def test_truncate_to_max_tokens(self) -> None:
        ctx = _Helpers.make_context([
            ("a" * 200, 0.9),
            ("b" * 200, 0.8),
        ])
        compressor = ContextCompressor(CompressionConfig(
            strategy=CompressionStrategy.TRUNCATE,
            max_tokens=10,
        ))
        result = await compressor.compress(ctx)
        assert result.total_tokens <= 10

    async def test_empty_context(self) -> None:
        ctx = AssembledContext()
        compressor = ContextCompressor()
        result = await compressor.compress(ctx)
        assert result.document_count == 0

    async def test_event_publisher_called(self) -> None:
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        ctx = _Helpers.make_context([("content with enough text to survive compression", 0.9)])
        compressor = ContextCompressor(event_publisher=publisher)
        await compressor.compress(ctx)
        assert len(events) == 1
        assert events[0].original_tokens == ctx.total_tokens
        assert events[0].compressed_tokens >= 0

    async def test_summarize_single_doc_unchanged(self) -> None:
        ctx = _Helpers.make_context([("only one", 0.5)])
        compressor = ContextCompressor(CompressionConfig(
            strategy=CompressionStrategy.SUMMARIZE,
        ))
        result = await compressor.compress(ctx)
        assert result.document_count == 1
        assert result.documents[0].content == "only one"

    def test_config_property(self) -> None:
        cfg = CompressionConfig(strategy=CompressionStrategy.TRUNCATE)
        compressor = ContextCompressor(cfg)
        assert compressor.config.strategy is CompressionStrategy.TRUNCATE
