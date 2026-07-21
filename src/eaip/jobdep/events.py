"""Domain events for the job dependency manager."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class NodeRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.jobdep.node_registered"

    node_id: str
    name: str
    node_type: str


class DependencyCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.jobdep.dependency_created"

    dependency_id: str
    source_job_id: str
    target_job_id: str


class DependencyResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.jobdep.dependency_resolved"

    node_id: str
    dependency_count: int


class DAGUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.jobdep.dag_updated"

    graph_id: str
    node_count: int
    dependency_count: int


__all__ = [
    "DAGUpdated",
    "DependencyCreated",
    "DependencyResolved",
    "NodeRegistered",
]
