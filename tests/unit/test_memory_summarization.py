"""Tests for ExtractiveMemorySummarizer."""

from __future__ import annotations

import pytest

from eaip.memory.models import MemoryItem, MemoryScope, MemoryType
from eaip.memory.summarization import ExtractiveMemorySummarizer


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1")


@pytest.fixture
def summarizer() -> ExtractiveMemorySummarizer:
    return ExtractiveMemorySummarizer()


class TestExtractiveMemorySummarizer:
    @pytest.mark.asyncio
    async def test_summarize_single(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="hello world"
            ),
        ]
        result = await summarizer.summarize(memories, max_length=500)
        assert "hello world" in result

    @pytest.mark.asyncio
    async def test_summarize_multiple(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="first item",
                importance=0.8,
            ),
            MemoryItem(
                memory_id="m2",
                memory_type=MemoryType.SESSION,
                scope=scope,
                content="second item",
                importance=0.5,
            ),
        ]
        result = await summarizer.summarize(memories, max_length=200)
        assert "first" in result or "second" in result

    @pytest.mark.asyncio
    async def test_summarize_empty_list(self, summarizer: ExtractiveMemorySummarizer) -> None:
        result = await summarizer.summarize([], max_length=500)
        assert result == ""

    @pytest.mark.asyncio
    async def test_summarize_zero_max_length(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="hello"
            ),
        ]
        result = await summarizer.summarize(memories, max_length=0)
        assert result == ""

    @pytest.mark.asyncio
    async def test_summarize_respects_max_length(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="a" * 100
            ),
            MemoryItem(
                memory_id="m2", memory_type=MemoryType.SESSION, scope=scope, content="b" * 100
            ),
        ]
        result = await summarizer.summarize(memories, max_length=50)
        assert len(result) <= 50

    @pytest.mark.asyncio
    async def test_summarize_prioritizes_by_importance(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="low importance",
                importance=0.1,
            ),
            MemoryItem(
                memory_id="m2",
                memory_type=MemoryType.SESSION,
                scope=scope,
                content="HIGH IMPORTANCE",
                importance=0.9,
            ),
        ]
        result = await summarizer.summarize(memories, max_length=200)
        assert "HIGH IMPORTANCE" in result

    @pytest.mark.asyncio
    async def test_summarize_uses_content_summary(
        self, summarizer: ExtractiveMemorySummarizer, scope: MemoryScope
    ) -> None:
        memories = [
            MemoryItem(
                memory_id="m1",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="very long content that should not appear in the summary",
                content_summary="short summary",
            ),
        ]
        result = await summarizer.summarize(memories, max_length=200)
        assert "short summary" in result


class TestSlidingWindowTokenCompressor:
    def test_compress_messages_within_budget(self) -> None:
        from eaip.memory.summarization import SlidingWindowTokenCompressor

        compressor = SlidingWindowTokenCompressor(target_max_tokens=100)
        messages = [
            {"role": "system", "content": "System directive"},
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = compressor.compress_messages(messages)
        assert len(result) == 3

    def test_compress_messages_exceeding_budget(self) -> None:
        from eaip.memory.summarization import SlidingWindowTokenCompressor

        compressor = SlidingWindowTokenCompressor(target_max_tokens=10)
        messages = [
            {"role": "system", "content": "Sys"},
            {"role": "user", "content": "Old message " * 10},
            {"role": "assistant", "content": "Old reply " * 10},
            {"role": "user", "content": "Recent short query"},
        ]
        result = compressor.compress_messages(messages)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["content"] == "Recent short query"

