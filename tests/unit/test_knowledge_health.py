from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.knowledge.health import KnowledgeHealthCheck
from eaip.knowledge.models import DocumentFormat, KnowledgeCollection, KnowledgeDocument
from eaip.knowledge.registry import KnowledgeRegistry


class TestKnowledgeHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_empty(self) -> None:
        registry = KnowledgeRegistry()
        check = KnowledgeHealthCheck(registry)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "knowledge"

    @pytest.mark.asyncio
    async def test_healthy_with_collections(self) -> None:
        registry = KnowledgeRegistry()
        col = KnowledgeCollection(collection_id="col:test", name="test")
        registry.register_collection(col)
        doc = KnowledgeDocument(document_id="d1", collection="test", format=DocumentFormat.TXT)
        registry.register_document(doc)
        check = KnowledgeHealthCheck(registry)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["collections"] == 1
        assert report.details["documents"] == 1
