"""JobDependencyManager — DAG-based job dependency resolution and lifecycle management."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.jobdep.events import (
    DAGUpdated,
    DependencyCreated,
    DependencyResolved,
    NodeRegistered,
)
from eaip.jobdep.exceptions import CircularDependencyError, NodeNotFoundError
from eaip.jobdep.models import (
    DAGGraph,
    DependencyType,
    JobDepConfig,
    JobDependency,
    JobNode,
    NodeStatus,
)

EventCallback = Callable[[Any], Any]


class JobDependencyManager:
    def __init__(
        self,
        config: JobDepConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or JobDepConfig()
        self._nodes: dict[str, JobNode] = {}
        self._dependencies: dict[str, JobDependency] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def register_node(
        self,
        name: str,
        *,
        node_type: str = "default",
        metadata: dict[str, object] | None = None,
    ) -> JobNode:
        node = JobNode(
            id=str(uuid.uuid4()),
            name=name,
            type=node_type,
            metadata=metadata or {},
        )
        self._nodes[node.id] = node
        self._emit(
            NodeRegistered(
                node_id=node.id,
                name=name,
                node_type=node_type,
            )
        )
        self._notify_dag_updated()
        return node

    async def get_node(self, node_id: str) -> JobNode:
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return self._nodes[node_id]

    async def create_dependency(
        self,
        source_job_id: str,
        target_job_id: str,
        *,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        lag_minutes: int = 0,
    ) -> JobDependency:
        if source_job_id not in self._nodes:
            raise NodeNotFoundError(source_job_id)
        if target_job_id not in self._nodes:
            raise NodeNotFoundError(target_job_id)

        if self._config.enable_cycle_detection:
            if self._would_create_cycle(source_job_id, target_job_id):
                raise CircularDependencyError(source_job_id, target_job_id)

        dependency = JobDependency(
            id=str(uuid.uuid4()),
            source_job_id=source_job_id,
            target_job_id=target_job_id,
            dependency_type=dependency_type,
            lag_minutes=lag_minutes,
        )
        self._dependencies[dependency.id] = dependency
        self._emit(
            DependencyCreated(
                dependency_id=dependency.id,
                source_job_id=source_job_id,
                target_job_id=target_job_id,
            )
        )
        self._notify_dag_updated()

        if self._config.auto_resolve_ready:
            await self._resolve_ready(target_job_id)

        return dependency

    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        visited: set[str] = set()

        def dfs(current: str) -> bool:
            if current == source_id:
                return True
            if current in visited:
                return False
            visited.add(current)
            for dep in self._dependencies.values():
                if dep.source_job_id == current:
                    if dfs(dep.target_job_id):
                        return True
            return False

        return dfs(target_id)

    async def _resolve_ready(self, node_id: str) -> None:
        unsatisfied = [dep for dep in self._dependencies.values() if dep.target_job_id == node_id]
        all_satisfied = all(
            self._nodes[dep.source_job_id].status == NodeStatus.COMPLETED
            for dep in unsatisfied
            if dep.source_job_id in self._nodes
        )

        if all_satisfied and node_id in self._nodes:
            node = self._nodes[node_id]
            if node.status == NodeStatus.PENDING:
                updated = JobNode(
                    id=node.id,
                    name=node.name,
                    type=node.type,
                    status=NodeStatus.READY,
                    metadata=node.metadata,
                    created_at=node.created_at,
                )
                self._nodes[node_id] = updated
                self._emit(
                    DependencyResolved(
                        node_id=node_id,
                        dependency_count=len(unsatisfied),
                    )
                )

    async def update_node_status(
        self,
        node_id: str,
        status: NodeStatus,
    ) -> JobNode:
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        node = self._nodes[node_id]
        updated = JobNode(
            id=node.id,
            name=node.name,
            type=node.type,
            status=status,
            metadata=node.metadata,
            created_at=node.created_at,
        )
        self._nodes[node_id] = updated

        if status == NodeStatus.COMPLETED:
            dependents = [
                dep for dep in self._dependencies.values() if dep.source_job_id == node_id
            ]
            for dep in dependents:
                await self._resolve_ready(dep.target_job_id)

        return updated

    def get_graph(self) -> DAGGraph:
        return DAGGraph(
            nodes=tuple(self._nodes.values()),
            dependencies=tuple(self._dependencies.values()),
        )

    def _notify_dag_updated(self) -> None:
        graph = self.get_graph()
        self._emit(
            DAGUpdated(
                graph_id="default",
                node_count=len(graph.nodes),
                dependency_count=len(graph.dependencies),
            )
        )


__all__ = ["JobDependencyManager"]
