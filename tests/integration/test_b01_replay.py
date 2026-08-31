"""B01 — event replay verification.

Replay handlers receive the *stored* event representation (a dict with
``id``, ``event_type``, ``payload``, ``metadata``, ``tenant_id``,
``occurred_at``), matching the :mod:`eaip.events.replay` contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from eaip.events.event import DomainEvent
from eaip.events.replay import EventReplay, ReplayResult
from eaip.events.store_pg import PgEventStore


class _FileImported(DomainEvent):
    event_type = "test.file_imported"
    file_name: str


class _UserInvited(DomainEvent):
    event_type = "test.user_invited"
    email: str


class TestEventReplay:
    async def _seed(
        self, store: PgEventStore, base: datetime, tenant: str = "acme"
    ) -> None:
        for i in range(3):
            await store.record(
                _FileImported(
                    file_name=f"f{i}",
                    occurred_at=base + timedelta(seconds=i),
                    tenant_id=tenant,
                )
            )
        await store.record(
            _UserInvited(email="x@example.com", occurred_at=base + timedelta(seconds=5))
        )

    def _make(self) -> tuple[EventReplay, PgEventStore]:
        store = PgEventStore()
        return EventReplay(store=store), store

    async def test_replay_all(self, db: None) -> None:
        replay, store = self._make()
        await self._seed(store, datetime.now(UTC))
        seen: list[dict[str, Any]] = []

        async def handler(event: dict[str, Any]) -> None:
            seen.append(event)

        result = await replay.replay_since(datetime.now(UTC) - timedelta(hours=1), handler)
        assert isinstance(result, ReplayResult)
        assert result.total == 4
        assert result.failed == 0
        assert len([e for e in seen if e["event_type"] == "_FileImported"]) == 3

    async def test_replay_by_type(self, db: None) -> None:
        replay, store = self._make()
        await self._seed(store, datetime.now(UTC))
        seen: list[str] = []

        async def handler(event: dict[str, Any]) -> None:
            seen.append(event["payload"]["file_name"])

        result = await replay.replay_by_type("_FileImported", handler)
        assert result.total == 3
        assert set(seen) == {"f0", "f1", "f2"}

    async def test_replay_for_tenant(self, db: None) -> None:
        replay, store = self._make()
        base = datetime.now(UTC)
        await store.record(_FileImported(file_name="acme.txt", occurred_at=base, tenant_id="acme"))
        await store.record(
            _FileImported(file_name="globex.txt", occurred_at=base, tenant_id="globex")
        )
        seen: list[str] = []

        async def handler(event: dict[str, Any]) -> None:
            seen.append(event["payload"]["file_name"])

        result = await replay.replay_for_tenant("acme", handler)
        assert result.total == 1
        assert seen == ["acme.txt"]

    async def test_replay_range(self, db: None) -> None:
        replay, store = self._make()
        base = datetime.now(UTC)
        await self._seed(store, base)
        seen: list[str] = []

        async def handler(event: dict[str, Any]) -> None:
            seen.append(event["payload"].get("file_name", ""))

        result = await replay.replay_range(
            base - timedelta(seconds=1),
            base + timedelta(seconds=4),
            handler,
        )
        assert result.total == 3
        assert seen == ["f0", "f1", "f2"]

    async def test_failed_handler_counted(self, db: None) -> None:
        replay, store = self._make()
        base = datetime.now(UTC)
        await store.record(_FileImported(file_name="x", occurred_at=base))

        async def bad(_event: dict[str, Any]) -> None:
            raise ValueError("replay handler failed")

        result = await replay.replay_since(base - timedelta(minutes=1), bad)
        assert result.failed == 1
        assert len(result.failures) == 1

    async def test_replay_does_not_duplicate_events(self, db: None) -> None:
        replay, store = self._make()
        base = datetime.now(UTC)
        await self._seed(store, base)
        seen: list[str] = []

        async def handler(event: dict[str, Any]) -> None:
            seen.append(event["id"])

        await replay.replay_range(
            base - timedelta(seconds=1), base + timedelta(seconds=10), handler
        )
        await replay.replay_range(
            base - timedelta(seconds=1), base + timedelta(seconds=10), handler
        )
        assert len(seen) == 8