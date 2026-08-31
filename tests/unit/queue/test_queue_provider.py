from __future__ import annotations

import pytest

from eaip.queue.exceptions import QueueClosedError, QueueFullError
from eaip.queue.models import QueueConfig, QueueMessage
from eaip.queue.provider import InMemoryQueue


@pytest.fixture
def queue() -> InMemoryQueue:
    config = QueueConfig(name="test", max_size=100)
    return InMemoryQueue(config)


@pytest.fixture
def message() -> QueueMessage:
    return QueueMessage(message_id="m1", payload=b"hello")


class TestInMemoryQueue:
    @pytest.mark.asyncio
    async def test_enqueue(self, queue: InMemoryQueue, message: QueueMessage) -> None:
        await queue.enqueue(message)
        stats = await queue.get_stats()
        assert stats.current_depth == 1
        assert stats.total_enqueued == 1

    @pytest.mark.asyncio
    async def test_dequeue(self, queue: InMemoryQueue, message: QueueMessage) -> None:
        await queue.enqueue(message)
        msg = await queue.dequeue("consumer1", timeout=1.0)
        assert msg is not None
        assert msg.message_id == "m1"

    @pytest.mark.asyncio
    async def test_dequeue_empty(self, queue: InMemoryQueue) -> None:
        msg = await queue.dequeue("c1", timeout=0.1)
        assert msg is None

    @pytest.mark.asyncio
    async def test_acknowledge(self, queue: InMemoryQueue, message: QueueMessage) -> None:
        await queue.enqueue(message)
        await queue.dequeue("c1", timeout=1.0)
        result = await queue.acknowledge("m1")
        assert result is True

    @pytest.mark.asyncio
    async def test_acknowledge_not_found(self, queue: InMemoryQueue) -> None:
        result = await queue.acknowledge("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_peek(self, queue: InMemoryQueue, message: QueueMessage) -> None:
        await queue.enqueue(message)
        messages = await queue.peek(10)
        assert len(messages) == 1
        assert messages[0].message_id == "m1"

    @pytest.mark.asyncio
    async def test_purge(self, queue: InMemoryQueue, message: QueueMessage) -> None:
        await queue.enqueue(message)
        count = await queue.purge()
        assert count == 1
        stats = await queue.get_stats()
        assert stats.current_depth == 0

    @pytest.mark.asyncio
    async def test_close(self, queue: InMemoryQueue) -> None:
        await queue.close()
        with pytest.raises(QueueClosedError):
            await queue.enqueue(QueueMessage(message_id="m2", payload=b"x"))

    @pytest.mark.asyncio
    async def test_queue_full(self) -> None:
        config = QueueConfig(name="small", max_size=1)
        q = InMemoryQueue(config)
        await q.enqueue(QueueMessage(message_id="m1", payload=b"x"))
        with pytest.raises(QueueFullError):
            await q.enqueue(QueueMessage(message_id="m2", payload=b"x"))

    def test_config_property(self, queue: InMemoryQueue) -> None:
        assert queue.config.name == "test"
