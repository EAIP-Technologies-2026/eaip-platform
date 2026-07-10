"""Tests for WorkerRegistry."""

from __future__ import annotations

import pytest

from eaip.workforce.exceptions import WorkerNotFoundError
from eaip.workforce.models import WorkerDefinition, WorkerType
from eaip.workforce.worker import WorkerRegistry


class TestWorkerRegistry:
    def test_register_worker(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        result = reg.register_worker(w)
        assert result is w
        assert reg.get_worker("w1") is w

    def test_register_worker_overwrite(self) -> None:
        reg = WorkerRegistry()
        w1 = WorkerDefinition(id="w1", name="First", worker_type=WorkerType.AGENT)
        w2 = WorkerDefinition(id="w1", name="Second", worker_type=WorkerType.AGENT)
        reg.register_worker(w1)
        reg.register_worker(w2)
        assert reg.get_worker("w1").name == "Second"

    def test_unregister_worker(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        reg.register_worker(w)
        reg.unregister_worker("w1")
        with pytest.raises(WorkerNotFoundError):
            reg.get_worker("w1")

    def test_unregister_worker_not_found(self) -> None:
        reg = WorkerRegistry()
        with pytest.raises(WorkerNotFoundError):
            reg.unregister_worker("nonexistent")

    def test_get_worker(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        reg.register_worker(w)
        assert reg.get_worker("w1") == w

    def test_get_worker_not_found(self) -> None:
        reg = WorkerRegistry()
        with pytest.raises(WorkerNotFoundError):
            reg.get_worker("nonexistent")

    def test_list_workers_all(self) -> None:
        reg = WorkerRegistry()
        w1 = WorkerDefinition(id="w1", name="A", worker_type=WorkerType.AGENT)
        w2 = WorkerDefinition(id="w2", name="B", worker_type=WorkerType.WORKFLOW)
        w3 = WorkerDefinition(id="w3", name="C", worker_type=WorkerType.JOB)
        reg.register_worker(w1)
        reg.register_worker(w2)
        reg.register_worker(w3)
        all_workers = reg.list_workers()
        assert len(all_workers) == 3

    def test_list_workers_by_type(self) -> None:
        reg = WorkerRegistry()
        w1 = WorkerDefinition(id="w1", name="A", worker_type=WorkerType.AGENT)
        w2 = WorkerDefinition(id="w2", name="B", worker_type=WorkerType.WORKFLOW)
        reg.register_worker(w1)
        reg.register_worker(w2)
        agents = reg.list_workers(worker_type=WorkerType.AGENT)
        assert len(agents) == 1
        assert agents[0].id == "w1"

    def test_count_available_all_available(self) -> None:
        reg = WorkerRegistry()
        w1 = WorkerDefinition(id="w1", name="A", worker_type=WorkerType.AGENT, max_concurrent_runs=2)
        w2 = WorkerDefinition(id="w2", name="B", worker_type=WorkerType.AGENT, max_concurrent_runs=1)
        reg.register_worker(w1)
        reg.register_worker(w2)
        assert reg.count_available() == 2

    def test_count_available_some_busy(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="A", worker_type=WorkerType.AGENT, max_concurrent_runs=2)
        reg.register_worker(w)
        reg.increment_active("w1")
        reg.increment_active("w1")
        assert reg.count_available() == 0

    def test_increment_active(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        reg.register_worker(w)
        assert reg.increment_active("w1") == 1
        assert reg.increment_active("w1") == 2
        assert reg.active_count("w1") == 2

    def test_decrement_active(self) -> None:
        reg = WorkerRegistry()
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        reg.register_worker(w)
        reg.increment_active("w1")
        reg.increment_active("w1")
        assert reg.decrement_active("w1") == 1
        assert reg.decrement_active("w1") == 0
        assert reg.decrement_active("w1") == 0

    def test_active_count_default(self) -> None:
        reg = WorkerRegistry()
        assert reg.active_count("nonexistent") == 0

    def test_empty_registry(self) -> None:
        reg = WorkerRegistry()
        assert reg.list_workers() == []
        assert reg.count_available() == 0
