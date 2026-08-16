"""B01 — Qdrant lifecycle and tenant collection naming verification."""

from __future__ import annotations

import pytest

from eaip.knowledge.qdrant_store import QdrantStore


class TestTenantNaming:
    """Pure helpers — no Qdrant server required."""

    def test_tenant_collection_name(self) -> None:
        assert QdrantStore.tenant_collection_name("acme", "kb") == "eaip_acme_kb"

    def test_tenant_collection_name_sanitized(self) -> None:
        name = QdrantStore.tenant_collection_name("x" * 100, "kb")
        assert len(name) <= 63

    def test_tenant_prefix(self) -> None:
        assert QdrantStore.tenant_prefix("acme") == "eaip_acme"


@pytest.mark.integration
class TestQdrantLifecycle:
    async def test_lifecycle_requires_client(self) -> None:
        try:
            import qdrant_client  # noqa: F401
        except ImportError:
            pytest.skip("qdrant_client not installed")
            return
        from eaip.knowledge.models import DocumentChunk, RetrievalQuery

        store = QdrantStore(host="localhost", port=6333, api_key=None)
        collection = QdrantStore.tenant_collection_name("acme", "kb")
        try:
            await store.delete_collection(collection)
            await store.create_collection(collection, dimensions=384)
            await store.upsert_points(
                collection,
                [
                    DocumentChunk(
                        chunk_id="c-1",
                        document_id="d-1",
                        collection=collection,
                        content="hello world",
                        embedding=(0.1, 0.2, 0.3),
                    )
                ],
            )
            hits = await store.search(
                collection,
                RetrievalQuery(query="hello", hybrid=False, top_k=1),
            )
            assert hits and hits[0]["id"] == "c-1"
            info = await store.collection_info(collection)
            assert info["points_count"] == 1
        finally:
            await store.delete_collection(collection)