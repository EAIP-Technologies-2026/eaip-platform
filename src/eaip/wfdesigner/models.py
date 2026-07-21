"""Workflow designer models — blueprints, nodes, edges, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class NodeType(StrEnum):
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"


class EdgeType(StrEnum):
    DEFAULT = "default"
    CONDITIONAL = "conditional"
    TIMEOUT = "timeout"


class WorkflowNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: NodeType
    label: str = ""
    config: dict[str, object] = Field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0


class WorkflowEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_node_id: str
    target_node_id: str
    label: str = ""
    edge_type: EdgeType = EdgeType.DEFAULT
    condition: str | None = None


class WorkflowBlueprint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    nodes: tuple[WorkflowNode, ...] = Field(default_factory=tuple)
    edges: tuple[WorkflowEdge, ...] = Field(default_factory=tuple)
    properties: dict[str, object] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DesignerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_nodes_per_blueprint: int = Field(default=200, ge=1)
    max_edges_per_blueprint: int = Field(default=400, ge=1)
    enable_drag_drop: bool = Field(default=True)
    enable_auto_layout: bool = Field(default=True)
    snap_to_grid: bool = Field(default=True)
    grid_size: float = Field(default=10.0, ge=1.0)


__all__ = [
    "DesignerConfig",
    "EdgeType",
    "NodeType",
    "WorkflowBlueprint",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowStatus",
]
