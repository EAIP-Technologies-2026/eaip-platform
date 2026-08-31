from __future__ import annotations

import pytest

from eaip.queue.exceptions import QueueError
from eaip.queue.manager import QueueManager
from eaip.queue.models import QueueConfig, QueueMessage


@pytest.fixture
def manager() -> QueueManager:
    return QueueManager()


class TestQueueManager:
    def test_create_queue(self, manager: QueueManager) -> None:
        config = QueueConfig(name="test")
        queue = manager.create_queue(config)
        assert queue is not None
        assert manager.get_queue("test") is queue

    def test_create_duplicate(self, manager: QueueManager) -> None:
        config = QueueConfig(name="test")
        manager.create_queue(config)
        with pytest.raises(QueueError):
            manager.create_queue(config)

    def test_create_with_dlq(self, manager: QueueManager) -> None:
        config = QueueConfig(name="orders", dead_letter_queue="orders-dlq")
        manager.create_queue(config)
        assert manager.get_queue("orders-dlq") is not None

    def test_get_queue_not_found(self, manager: QueueManager) -> None:
        assert manager.get_queue("nonexistent") is None

    def test_delete_queue(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="test"))
        assert manager.delete_queue("test") is True
        assert manager.get_queue("test") is None

    def test_delete_queue_not_found(self, manager: QueueManager) -> None:
        assert manager.delete_queue("nonexistent") is False

    def test_list_queues(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="q1"))
        manager.create_queue(QueueConfig(name="q2"))
        queues = manager.list_queues()
        assert sorted(queues) == ["q1", "q2"]

    @pytest.mark.asyncio
    async def test_enqueue_to(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="test"))
        msg = QueueMessage(message_id="m1", payload=b"data")
        await manager.enqueue_to("test", msg)
        queue = manager.get_queue("test")
        stats = await queue.get_stats()
        assert stats.current_depth == 1

    @pytest.mark.asyncio
    async def test_enqueue_to_not_found(self, manager: QueueManager) -> None:
        msg = QueueMessage(message_id="m1", payload=b"data")
        with pytest.raises(QueueError):
            await manager.enqueue_to("nonexistent", msg)

    @pytest.mark.asyncio
    async def test_route_message(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="src"))
        manager.create_queue(QueueConfig(name="dst"))
        msg = QueueMessage(message_id="m1", payload=b"data")
        await manager.enqueue_to("src", msg)
        result = await manager.route_message("src", "dst", "m1")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_dlq_messages(self, manager: QueueManager) -> None:
        config = QueueConfig(name="orders", dead_letter_queue="orders-dlq")
        manager.create_queue(config)
        dlq = await manager.get_dlq_messages("orders")
        assert dlq == []

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="test"))
        stats = await manager.get_queue_stats("test")
        assert stats is not None
        assert stats.current_depth == 0

    @pytest.mark.asyncio
    async def test_get_queue_stats_not_found(self, manager: QueueManager) -> None:
        stats = await manager.get_queue_stats("nonexistent")
        assert stats is None

    @pytest.mark.asyncio
    async def test_close_all(self, manager: QueueManager) -> None:
        manager.create_queue(QueueConfig(name="q1"))
        manager.create_queue(QueueConfig(name="q2"))
        await manager.close_all()
        assert manager.list_queues() == []
