from __future__ import annotations

import pytest

from eaip.compliance.evidence import EvidenceCollector


class TestEvidenceCollector:
    @pytest.fixture
    def collector(self) -> EvidenceCollector:
        return EvidenceCollector()

    @pytest.mark.asyncio
    async def test_collect(self, collector: EvidenceCollector) -> None:
        record = await collector.collect("c1", "audit", {"key": "val"}, "tester")
        assert record.control_id == "c1"
        assert record.source == "audit"
        assert record.data["key"] == "val"
        assert record.collected_by == "tester"
        assert record.valid is True

    @pytest.mark.asyncio
    async def test_collect_defaults(self, collector: EvidenceCollector) -> None:
        record = await collector.collect("c1", "audit")
        assert record.data == {}
        assert record.collected_by == "unknown"
        assert record.valid is True

    @pytest.mark.asyncio
    async def test_collect_from_audit(self, collector: EvidenceCollector) -> None:
        record = await collector.collect_from_audit("c1", {"finding": "pass"})
        assert record.source == "audit"
        assert record.collected_by == "evidence.audit"
        assert record.data["finding"] == "pass"

    @pytest.mark.asyncio
    async def test_collect_from_policy(self, collector: EvidenceCollector) -> None:
        record = await collector.collect_from_policy("c2", {"policy": "ok"})
        assert record.source == "policy"
        assert record.collected_by == "evidence.policy"
        assert record.data["policy"] == "ok"

    @pytest.mark.asyncio
    async def test_collect_from_datamask(self, collector: EvidenceCollector) -> None:
        record = await collector.collect_from_datamask("c3", {"masked": True})
        assert record.source == "datamask"
        assert record.collected_by == "evidence.datamask"
        assert record.data["masked"] is True

    @pytest.mark.asyncio
    async def test_get_evidence_found(self, collector: EvidenceCollector) -> None:
        record = await collector.collect("c1", "audit")
        found = collector.get_evidence(record.evidence_id)
        assert found is not None
        assert found.evidence_id == record.evidence_id

    @pytest.mark.asyncio
    async def test_get_evidence_not_found(self, collector: EvidenceCollector) -> None:
        assert collector.get_evidence("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_evidence_for_control(self, collector: EvidenceCollector) -> None:
        await collector.collect("c1", "audit")
        await collector.collect("c1", "policy")
        await collector.collect("c2", "audit")
        records = collector.get_evidence_for_control("c1")
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_evidence_for_control_empty(self, collector: EvidenceCollector) -> None:
        assert collector.get_evidence_for_control("nonexistent") == ()

    @pytest.mark.asyncio
    async def test_invalidate_evidence(self, collector: EvidenceCollector) -> None:
        record = await collector.collect("c1", "audit")
        invalidated = collector.invalidate_evidence(record.evidence_id)
        assert invalidated is not None
        assert invalidated.valid is False

    @pytest.mark.asyncio
    async def test_invalidate_evidence_not_found(self, collector: EvidenceCollector) -> None:
        assert collector.invalidate_evidence("nonexistent") is None

    @pytest.mark.asyncio
    async def test_count(self, collector: EvidenceCollector) -> None:
        assert collector.count() == 0
        await collector.collect("c1", "audit")
        assert collector.count() == 1

    @pytest.mark.asyncio
    async def test_clear(self, collector: EvidenceCollector) -> None:
        await collector.collect("c1", "audit")
        collector.clear()
        assert collector.count() == 0
