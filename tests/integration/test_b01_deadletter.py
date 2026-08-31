"""B01 — dead-letter queue verification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.events.deadletter import DeadLetterQueue
from eaip.events.event import DomainEvent


class _PaymentFailed(DomainEvent):
    event_type = "test.payment_failed"
    amount: float


class TestDeadLetterQueue:
    async def test_record_and_get(self, db: None) -> None:
        dlq = DeadLetterQueue()
        event = _PaymentFailed(amount=99.0, tenant_id="acme")
        letter_id = await dlq.record(event, "billing.on_failure", ValueError("declined"))
        letter = await dlq.get(letter_id)
        assert letter is not None
        assert letter["event_id"] == event.id
        assert letter["tenant_id"] == "acme"
        assert letter["handler_name"] == "billing.on_failure"
        assert "declined" in letter["error_message"]
        assert letter["resolved"] is False
        assert letter["event_type"] == "_PaymentFailed"

    async def test_recent_and_unresolved(self, db: None) -> None:
        dlq = DeadLetterQueue()
        for _ in range(2):
            await dlq.record(_PaymentFailed(amount=1.0), "h", RuntimeError("nope"))
        assert len(await dlq.recent()) == 2
        assert len(await dlq.unresolved()) == 2
        assert await dlq.count(unresolved_only=True) == 2

    async def test_retry_success_resolves(self, db: None) -> None:
        dlq = DeadLetterQueue()
        event = _PaymentFailed(amount=5.0, tenant_id="acme")
        letter_id = await dlq.record(event, "billing.handler", RuntimeError("transient"))
        seen: list[dict] = []

        async def handler(payload: dict) -> None:
            seen.append(payload)

        assert await dlq.retry(letter_id, handler) is True
        assert len(seen) == 1
        assert seen[0]["amount"] == 5.0
        assert (await dlq.get(letter_id))["resolved"] is True

    async def test_retry_failure_increments(self, db: None) -> None:
        dlq = DeadLetterQueue()
        letter_id = await dlq.record(
            _PaymentFailed(amount=1.0), "billing.handler", RuntimeError("boom")
        )

        async def handler(_payload: dict) -> None:
            raise RuntimeError("still broken")

        assert await dlq.retry(letter_id, handler) is False
        letter = await dlq.get(letter_id)
        assert letter["retry_count"] == 1
        assert letter["resolved"] is False
        assert letter["last_retry_at"] is not None

    async def test_purge(self, db: None) -> None:
        dlq = DeadLetterQueue()
        await dlq.record(_PaymentFailed(amount=1.0), "h", RuntimeError("old"))
        removed = await dlq.purge(datetime.now(UTC) + timedelta(days=1))
        assert removed == 1
        assert await dlq.count() == 0

    async def test_purge_keeps_recent(self, db: None) -> None:
        dlq = DeadLetterQueue()
        await dlq.record(_PaymentFailed(amount=1.0), "h", RuntimeError("new"))
        removed = await dlq.purge(datetime.now(UTC) - timedelta(days=1))
        assert removed == 0
        assert await dlq.count() == 1

    async def test_tenant_id_preserved(self, db: None) -> None:
        dlq = DeadLetterQueue()
        letter_id = await dlq.record(
            _PaymentFailed(amount=1.0, tenant_id="globex"), "h", RuntimeError("x")
        )
        assert (await dlq.get(letter_id))["tenant_id"] == "globex"