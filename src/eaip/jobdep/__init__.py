"""Job Dependency Manager — DAG-based job dependency resolution, scheduling, and lifecycle management."""

from __future__ import annotations

from eaip.jobdep.events import (
    DAGUpdated,
    DependencyCreated,
    DependencyResolved,
    NodeRegistered,
)
from eaip.jobdep.exceptions import (
    CircularDependencyError,
    JobDepError,
    NodeNotFoundError,
)
from eaip.jobdep.health import JobDepHealthCheck
from eaip.jobdep.integration import JobDepRuntimeModule
from eaip.jobdep.manager import JobDependencyManager
from eaip.jobdep.models import (
    DAGGraph,
    DependencyType,
    JobDepConfig,
    JobDependency,
    JobNode,
    NodeStatus,
)

__all__ = [
    "CircularDependencyError",
    "DAGGraph",
    "DAGUpdated",
    "DependencyCreated",
    "DependencyResolved",
    "DependencyType",
    "JobDepConfig",
    "JobDepError",
    "JobDepHealthCheck",
    "JobDepRuntimeModule",
    "JobDependency",
    "JobDependencyManager",
    "JobNode",
    "NodeNotFoundError",
    "NodeRegistered",
    "NodeStatus",
]
