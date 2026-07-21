"""Tests for ChangeLogService."""

from __future__ import annotations

import pytest

from eaip.changelogsvc.models import ChangeAction, ChangeEntry, ChangeLogConfig, ChangeQuery
from eaip.changelogsvc.service import ChangeLogService


class TestChangeLogService:
    @pytest.mark.asyncio
    async def test_record(self) -> None:
        svc = ChangeLogService()
        entry = ChangeEntry(
            id="e1",
            resource_id="r1",
            resource_type="vm",
            action=ChangeAction.CREATED,
            changed_by="alice",
        )
        result = await svc.record(entry)
        assert result.id == "e1"
        assert await svc.count() == 1

    @pytest.mark.asyncio
    async def test_query_by_resource_id(self) -> None:
        svc = ChangeLogService()
        await svc.record(
            ChangeEntry(
                id="e1",
                resource_id="r1",
                resource_type="vm",
                action=ChangeAction.CREATED,
                changed_by="alice",
            )
        )
        await svc.record(
            ChangeEntry(
                id="e2",
                resource_id="r2",
                resource_type="vm",
                action=ChangeAction.UPDATED,
                changed_by="bob",
            )
        )
        results = await svc.query(ChangeQuery(resource_id="r1"))
        assert len(results) == 1
        assert results[0].id == "e1"

    @pytest.mark.asyncio
    async def test_query_pagination(self) -> None:
        svc = ChangeLogService()
        for i in range(10):
            await svc.record(
                ChangeEntry(
                    id=f"e{i}",
                    resource_id="r1",
                    resource_type="vm",
                    action=ChangeAction.UPDATED,
                    changed_by="alice",
                )
            )
        results = await svc.query(ChangeQuery(limit=3, offset=2))
        assert len(results) == 3
        assert results[0].id == "e2"

    @pytest.mark.asyncio
    async def test_config(self) -> None:
        cfg = ChangeLogConfig(retention_days=30)
        svc = ChangeLogService(config=cfg)
        assert svc.config.retention_days == 30
