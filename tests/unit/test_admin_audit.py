"""Tests for :mod:`eaip.admin.audit`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome


@pytest.fixture
def logger() -> AuditLogger:
    return AuditLogger()


@pytest.fixture
def sample_entries() -> list[AuditEntry]:
    now = datetime.now(timezone.utc)
    return [
        AuditEntry(
            id="e1",
            actor_id="alice",
            action="create",
            resource_type="plugin",
            resource_id="plugin-a",
            outcome=AuditOutcome.SUCCESS,
            timestamp=now - timedelta(hours=3),
        ),
        AuditEntry(
            id="e2",
            actor_id="bob",
            action="delete",
            resource_type="config",
            resource_id="cfg-1",
            outcome=AuditOutcome.FAILURE,
            timestamp=now - timedelta(hours=2),
        ),
        AuditEntry(
            id="e3",
            actor_id="alice",
            action="update",
            resource_type="plugin",
            resource_id="plugin-b",
            outcome=AuditOutcome.SUCCESS,
            timestamp=now - timedelta(hours=1),
        ),
    ]


class TestAuditLogger:
    async def test_log_and_query_all(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        results = logger.query()
        assert len(results) == 3

    async def test_query_filter_by_actor(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        results = logger.query(actor="alice")
        assert len(results) == 2
        assert all(r.actor_id == "alice" for r in results)

    async def test_query_filter_by_action(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        results = logger.query(action="delete")
        assert len(results) == 1
        assert results[0].id == "e2"

    async def test_query_filter_by_resource_type(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        results = logger.query(resource_type="config")
        assert len(results) == 1
        assert results[0].id == "e2"

    async def test_query_filter_by_time_range(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        now = datetime.now(timezone.utc)
        for e in sample_entries:
            logger.log(e)
        start = now - timedelta(hours=2, minutes=30)
        end = now - timedelta(minutes=30)
        results = logger.query(start=start, end=end)
        assert len(results) == 2

    async def test_query_returns_empty_when_no_match(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        results = logger.query(actor="nobody")
        assert results == []

    async def test_export_time_range(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        now = datetime.now(timezone.utc)
        for e in sample_entries:
            logger.log(e)
        start = now - timedelta(hours=4)
        end = now - timedelta(hours=2, minutes=30)
        results = logger.export(start, end)
        assert len(results) == 1
        assert results[0].id == "e1"

    async def test_export_chronological_order(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        now = datetime.now(timezone.utc)
        results = logger.export(now - timedelta(days=1), now + timedelta(days=1))
        timestamps = [r.timestamp for r in results]
        assert timestamps == sorted(timestamps)

    async def test_publish_without_event_bus(self, logger: AuditLogger) -> None:
        entry = AuditEntry(
            id="pub-1",
            actor_id="system",
            action="test",
            resource_type="audit",
            resource_id="self",
            outcome=AuditOutcome.SUCCESS,
        )
        await logger.publish(entry)
        assert len(logger.query()) == 1

    async def test_clear(self, logger: AuditLogger, sample_entries: list[AuditEntry]) -> None:
        for e in sample_entries:
            logger.log(e)
        logger.clear()
        assert logger.query() == []

    async def test_log_duplicate_id_overwrites(self, logger: AuditLogger) -> None:
        e1 = AuditEntry(
            id="dup",
            actor_id="alice",
            action="create",
            resource_type="plugin",
            resource_id="p1",
            outcome=AuditOutcome.SUCCESS,
        )
        e2 = AuditEntry(
            id="dup",
            actor_id="bob",
            action="delete",
            resource_type="config",
            resource_id="c1",
            outcome=AuditOutcome.FAILURE,
        )
        logger.log(e1)
        logger.log(e2)
        results = logger.query()
        assert len(results) == 1
        assert results[0].actor_id == "bob"
