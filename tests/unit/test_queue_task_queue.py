from __future__ import annotations

import pytest

from eaip.queue.task_queue import EnterpriseTaskQueue, Task, TaskPriority, TaskStatus


class TestEnterpriseTaskQueue:
    @pytest.fixture
    def queue(self) -> EnterpriseTaskQueue:
        return EnterpriseTaskQueue()

    def test_enqueue(self, queue: EnterpriseTaskQueue) -> None:
        task = Task(task_id="t1", name="test", priority=TaskPriority.HIGH)
        queue.enqueue(task)
        assert queue.get_queue_depth() == 1

    def test_enqueue_batch(self, queue: EnterpriseTaskQueue) -> None:
        tasks = [Task(task_id=f"t{i}", name=f"test{i}") for i in range(3)]
        queue.enqueue_batch(tasks)
        assert queue.get_queue_depth() == 3

    def test_dequeue(self, queue: EnterpriseTaskQueue) -> None:
        task = Task(task_id="t1", name="test", priority=TaskPriority.CRITICAL)
        queue.enqueue(task)
        dequeued = queue.dequeue("worker1")
        assert dequeued is not None
        assert dequeued.task_id == "t1"
        assert dequeued.status == TaskStatus.RUNNING

    def test_dequeue_empty(self, queue: EnterpriseTaskQueue) -> None:
        result = queue.dequeue("worker1")
        assert result is None

    def test_priority_ordering(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="low", priority=TaskPriority.LOW))
        queue.enqueue(Task(task_id="t2", name="critical", priority=TaskPriority.CRITICAL))
        t1 = queue.dequeue("w1")
        assert t1 is not None
        assert t1.task_id == "t2"

    def test_complete(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="test"))
        queue.dequeue("w1")
        result = queue.complete("t1")
        assert result is True
        task = queue.get_task("t1")
        assert task is not None
        assert task.status == TaskStatus.COMPLETED

    def test_fail_with_retry(self, queue: EnterpriseTaskQueue) -> None:
        task = Task(task_id="t1", name="test")
        task.max_retries = 1
        queue.enqueue(task)
        queue.dequeue("w1")
        result = queue.fail("t1", "error")
        assert result is True
        assert task.retry_count == 1
        assert task.status == TaskStatus.PENDING

    def test_fail_exhaust_retries(self, queue: EnterpriseTaskQueue) -> None:
        task = Task(task_id="t1", name="test")
        task.max_retries = 0
        queue.enqueue(task)
        queue.dequeue("w1")
        queue.fail("t1", "error")
        assert task.status == TaskStatus.FAILED

    def test_peek(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="test"))
        queue.enqueue(Task(task_id="t2", name="test2"))
        peeked = queue.peek(limit=1)
        assert len(peeked) == 1

    def test_list_tasks(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="test"))
        assert len(queue.list_tasks()) == 1
        assert len(queue.list_tasks(status=TaskStatus.PENDING)) == 1
        assert len(queue.list_tasks(status=TaskStatus.COMPLETED)) == 0

    def test_worker_count(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="test"))
        queue.dequeue("worker1")
        assert queue.get_worker_count() == 1

    def test_get_task(self, queue: EnterpriseTaskQueue) -> None:
        queue.enqueue(Task(task_id="t1", name="test"))
        task = queue.get_task("t1")
        assert task is not None
        assert queue.get_task("nonexistent") is None
