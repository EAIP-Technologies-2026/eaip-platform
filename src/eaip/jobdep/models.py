"""Job dependency models — nodes, dependencies, DAG graph, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class NodeStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class DependencyType(StrEnum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"


class JobNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str = "default"
    status: NodeStatus = NodeStatus.PENDING
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class JobDependency(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_job_id: str
    target_job_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_minutes: int = 0


class DAGGraph(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    nodes: tuple[JobNode, ...] = Field(default_factory=tuple)
    dependencies: tuple[JobDependency, ...] = Field(default_factory=tuple)

    @property
    def is_empty(self) -> bool:
        return len(self.nodes) == 0

    def get_node(self, node_id: str) -> JobNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def get_dependencies_for(self, node_id: str) -> tuple[JobDependency, ...]:
        return tuple(d for d in self.dependencies if d.target_job_id == node_id)

    def get_dependents_of(self, node_id: str) -> tuple[JobDependency, ...]:
        return tuple(d for d in self.dependencies if d.source_job_id == node_id)


class JobDepConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_nodes_per_dag: int = Field(default=500, ge=1)
    max_dependencies_per_node: int = Field(default=50, ge=1)
    enable_cycle_detection: bool = Field(default=True)
    auto_resolve_ready: bool = Field(default=True)


__all__ = [
    "DAGGraph",
    "DependencyType",
    "JobDepConfig",
    "JobDependency",
    "JobNode",
    "NodeStatus",
]
