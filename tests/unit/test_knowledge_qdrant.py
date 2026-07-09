"""Tests for QdrantStore integration."""

from __future__ import annotations

import pytest

from eaip.knowledge.models import DocumentChunk, RetrievalQuery
from eaip.knowledge.qdrant_store import QdrantStore


class TestQdrantStore:
    @pytest.mark.asyncio
    async def test_not_connected_by_default(self) -> None:
        store = QdrantStore(host="localhost", port=6333)
        assert not store._is_connected

    @pytest.mark.asyncio
    async def test_collection_info_fails_not_connected(self) -> None:
        store = QdrantStore(host="localhost", port=6333)
        with pytest.raises(RuntimeError):
            await store.collection_info("nonexistent")
