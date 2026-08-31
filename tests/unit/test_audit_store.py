from __future__ import annotations

from datetime import UTC, datetime, timedelta

from eaip.audit.models import ActorType, AuditEvent
from eaip.audit.store import AuditStoreConfig, ImmutableAuditStore


def _make_event(
    event_id: str, actor_id: str = "user1", action: str = "login", **kw: object
) -> AuditEvent:
    ts = kw.get("timestamp", datetime.now(UTC))
    assert isinstance(ts, datetime)
    return AuditEvent(
        id=event_id,
        event_type="audit.event",
        actor_id=actor_id,
        actor_type=ActorType.USER,
        action=action,
        resource_type="system",
        resource_id="sys1",
        timestamp=ts,
    )


class TestImmutableAuditStore:
    def test_append_and_query(self) -> None:
        store = ImmutableAuditStore()
        event = _make_event("e1")
        store.append(event)
        results = store.query(actor="user1")
        assert len(results) == 1
        assert results[0].id == "e1"

    def test_query_with_filters(self) -> None:
        store = ImmutableAuditStore()
        now = datetime.now(UTC)
        for i in range(5):
            store.append(
                _make_event(
                    f"e{i}", actor_id="u1" if i < 3 else "u2", timestamp=now + timedelta(hours=i)
                )
            )
        assert len(store.query(actor="u1")) == 3
        assert len(store.query(actor="u2")) == 2
        assert len(store.query(action="login")) == 5

    def test_query_with_limit_and_offset(self) -> None:
        store = ImmutableAuditStore()
        now = datetime.now(UTC)
        for i in range(10):
            store.append(_make_event(f"e{i}", timestamp=now + timedelta(hours=i)))
        results = store.query(limit=3)
        assert len(results) == 3
        results = store.query(limit=3, offset=8)
        assert len(results) == 2

    def test_count(self) -> None:
        store = ImmutableAuditStore()
        for i in range(5):
            store.append(_make_event(f"e{i}"))
        assert store.count() == 5
        assert store.count(actor="user1") == 5
        assert store.count(actor="nonexistent") == 0

    def test_size(self) -> None:
        store = ImmutableAuditStore()
        assert store.size() == 0
        store.append(_make_event("e1"))
        assert store.size() == 1

    def test_cleanup_removes_old_events(self) -> None:
        config = AuditStoreConfig()
        config.retention_days = 30
        store = ImmutableAuditStore(config)
        now = datetime.now(UTC)
        store.append(_make_event("old", timestamp=now - timedelta(days=60)))
        store.append(_make_event("new", timestamp=now))
        removed = store.cleanup()
        assert removed == 1
        assert store.size() == 1
        assert store.query()[0].id == "new"

    def test_snapshot_creation(self) -> None:
        config = AuditStoreConfig()
        config.snapshot_interval = 3
        store = ImmutableAuditStore(config)
        now = datetime.now(UTC)
        for i in range(10):
            store.append(_make_event(f"e{i}", timestamp=now))
        assert store.get_snapshot_count() >= 3

    def test_get_snapshot(self) -> None:
        config = AuditStoreConfig()
        config.snapshot_interval = 5
        store = ImmutableAuditStore(config)
        now = datetime.now(UTC)
        for i in range(10):
            store.append(_make_event(f"e{i}", timestamp=now))
        snapshot = store.get_snapshot(5)
        assert snapshot is not None
        assert "snapshot" in snapshot
