"""WorkerRegistry — register, unregister, and query worker definitions."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.workforce.events import WorkerRegistered, WorkerUnregistered
from eaip.workforce.exceptions import WorkerNotFoundError
from eaip.workforce.models import WorkerDefinition, WorkerType


class WorkerRegistry:
    """Registry of available workers in the workforce."""

    def __init__(self, event_bus: Any = None) -> None:
        self._workers: dict[str, WorkerDefinition] = {}
        self._active_counts: dict[str, int] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.workforce.worker")

    def register_worker(self, definition: WorkerDefinition) -> WorkerDefinition:
        """Register a worker definition.

        Args:
            definition: The worker to register.

        Returns:
            The registered WorkerDefinition.
        """
        self._workers[definition.id] = definition
        self._active_counts.setdefault(definition.id, 0)
        self._log.info("worker.registered", worker_id=definition.id, worker_type=str(definition.worker_type))
        self._publish(
            WorkerRegistered(
                worker_id=definition.id,
                worker_name=definition.name,
                worker_type=str(definition.worker_type),
                tags=definition.tags,
                metadata=definition.metadata,
            ),
        )
        return definition

    def unregister_worker(self, worker_id: str) -> None:
        """Remove a worker from the registry.

        Args:
            worker_id: The worker to remove.

        Raises:
            WorkerNotFoundError: If the worker is not registered.
        """
        worker = self._workers.pop(worker_id, None)
        if worker is None:
            raise WorkerNotFoundError(worker_id)
        self._active_counts.pop(worker_id, None)
        self._log.info("worker.unregistered", worker_id=worker_id)
        self._publish(
            WorkerUnregistered(
                worker_id=worker_id,
                worker_name=worker.name,
                worker_type=str(worker.worker_type),
            ),
        )

    def get_worker(self, worker_id: str) -> WorkerDefinition:
        """Get a worker definition by ID.

        Args:
            worker_id: The worker ID.

        Returns:
            The WorkerDefinition.

        Raises:
            WorkerNotFoundError: If the worker is not found.
        """
        worker = self._workers.get(worker_id)
        if worker is None:
            raise WorkerNotFoundError(worker_id)
        return worker

    def list_workers(self, worker_type: WorkerType | None = None) -> list[WorkerDefinition]:
        """List registered workers, optionally filtered by type.

        Args:
            worker_type: Optional type filter.

        Returns:
            A list of WorkerDefinitions.
        """
        if worker_type is None:
            return list(self._workers.values())
        return [w for w in self._workers.values() if w.worker_type is worker_type]

    def count_available(self) -> int:
        """Count workers that are not at max capacity.

        Returns:
            Number of workers with capacity for more runs.
        """
        count = 0
        for worker_id, definition in self._workers.items():
            current = self._active_counts.get(worker_id, 0)
            if current < definition.max_concurrent_runs:
                count += 1
        return count

    def increment_active(self, worker_id: str) -> int:
        """Increment the active run count for a worker.

        Args:
            worker_id: The worker ID.

        Returns:
            The new active count.
        """
        current = self._active_counts.get(worker_id, 0)
        self._active_counts[worker_id] = current + 1
        return current + 1

    def decrement_active(self, worker_id: str) -> int:
        """Decrement the active run count for a worker.

        Args:
            worker_id: The worker ID.

        Returns:
            The new active count.
        """
        current = self._active_counts.get(worker_id, 0)
        self._active_counts[worker_id] = max(0, current - 1)
        return max(0, current - 1)

    def active_count(self, worker_id: str) -> int:
        """Get the active run count for a worker.

        Args:
            worker_id: The worker ID.

        Returns:
            The active run count.
        """
        return self._active_counts.get(worker_id, 0)

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["WorkerRegistry"]
