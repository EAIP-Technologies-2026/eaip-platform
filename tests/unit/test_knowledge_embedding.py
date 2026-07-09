from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider, ProviderEmbedding
from eaip.knowledge.exceptions import EmbeddingError
from eaip.knowledge.models import EmbeddingConfig


class TestMockEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_deterministic(self) -> None:
        provider = MockEmbeddingProvider(dimensions=4)
        result = await provider.embed(["hello", "world"])
        assert len(result) == 2
        for vec in result:
            assert len(vec) == 4
            assert all(0.0 <= v <= 1.0 for v in vec)

    @pytest.mark.asyncio
    async def test_embed_same_text_same_vector(self) -> None:
        provider = MockEmbeddingProvider(dimensions=8)
        r1 = await provider.embed(["hello"])
        r2 = await provider.embed(["hello"])
        assert r1[0] == r2[0]

    @pytest.mark.asyncio
    async def test_dimensions(self) -> None:
        provider = MockEmbeddingProvider(dimensions=768)
        assert provider.dimensions == 768

    @pytest.mark.asyncio
    async def test_empty_texts(self) -> None:
        provider = MockEmbeddingProvider()
        result = await provider.embed([])
        assert result == []


class TestProviderEmbedding:
    @pytest.mark.asyncio
    async def test_no_embed_fn_raises(self) -> None:
        config = EmbeddingConfig()
        provider = ProviderEmbedding(config)
        with pytest.raises(EmbeddingError):
            await provider.embed(["text"])

    @pytest.mark.asyncio
    async def test_with_embed_fn(self) -> None:
        async def dummy_embed(texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
            return [(0.1, 0.2, 0.3) for _ in texts]

        config = EmbeddingConfig(dimensions=3)
        provider = ProviderEmbedding(config, embed_fn=dummy_embed)
        result = await provider.embed(["a", "b"])
        assert len(result) == 2
        assert result[0] == (0.1, 0.2, 0.3)

    @pytest.mark.asyncio
    async def test_empty_input(self) -> None:
        async def dummy_embed(texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
            return []

        config = EmbeddingConfig()
        provider = ProviderEmbedding(config, embed_fn=dummy_embed)
        result = await provider.embed([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_embed(self) -> None:
        results: list = []

        async def dummy_embed(texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
            results.append(len(texts))
            return [(0.5,) for _ in texts]

        config = EmbeddingConfig(dimensions=1, batch_size=2)
        provider = ProviderEmbedding(config, embed_fn=dummy_embed)
        texts = ["a", "b", "c", "d", "e"]
        result = await provider.embed_batch(texts, batch_size=2)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_dimensions(self) -> None:
        config = EmbeddingConfig(dimensions=512)
        provider = ProviderEmbedding(config)
        assert provider.dimensions == 512
