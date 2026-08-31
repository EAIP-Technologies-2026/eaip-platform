"""Process designer models — process models, elements, connectors, and related types."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DesignElementType(StrEnum):
    """Types of elements available in the process designer."""

    START = "start"
    END = "end"
    TASK = "task"
    SUBPROCESS = "subprocess"
    DECISION = "decision"
    PARALLEL = "parallel"
    EVENT = "event"
    GATEWAY = "gateway"


class ProcessElement(BaseModel):
    """A single node or step within a process model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: DesignElementType
    label: str = ""
    description: str = ""
    config: dict[str, object] = Field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0
    width: float = 120.0
    height: float = 60.0
    swimlane_id: str | None = None


class ProcessConnector(BaseModel):
    """A directed connection between two process elements."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_element_id: str
    target_element_id: str
    label: str = ""
    condition: str | None = None
    priority: int = 0
    is_default: bool = False


class ProcessSwimLane(BaseModel):
    """A horizontal lane grouping related process elements by role or department."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    label: str = ""
    color: str = "#e0e0e0"
    order: int = 0


class ProcessAnnotation(BaseModel):
    """A textual note attached to the process diagram or a specific element."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    text: str
    element_id: str | None = None
    position_x: float = 0.0
    position_y: float = 0.0


class ValidationResult(BaseModel):
    """Result of validating a process model, including errors and warnings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_valid: bool
    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)


class ProcessSimulationConfig(BaseModel):
    """Configuration for running a discrete-event simulation on a process model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = False
    iterations: int = Field(default=1000, ge=1)
    max_concurrent: int = Field(default=10, ge=1)
    arrival_rate: float = Field(default=1.0, ge=0.0)
    seed: int | None = None


class PaletteItem(BaseModel):
    """An item in the designer palette that can be dragged onto the canvas."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: DesignElementType
    label: str = ""
    icon: str = ""
    category: str = "default"


class DesignTemplate(BaseModel):
    """A reusable template containing pre-configured elements, connectors, and swimlanes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    elements: tuple[ProcessElement, ...] = Field(default_factory=tuple)
    connectors: tuple[ProcessConnector, ...] = Field(default_factory=tuple)
    swimlanes: tuple[ProcessSwimLane, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)


class ProcessModel(BaseModel):
    """A complete process model containing elements, connectors, swimlanes, and annotations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    version: int = 1
    elements: tuple[ProcessElement, ...] = Field(default_factory=tuple)
    connectors: tuple[ProcessConnector, ...] = Field(default_factory=tuple)
    swimlanes: tuple[ProcessSwimLane, ...] = Field(default_factory=tuple)
    annotations: tuple[ProcessAnnotation, ...] = Field(default_factory=tuple)
    properties: dict[str, object] = Field(default_factory=dict)
    simulation_config: ProcessSimulationConfig = Field(default_factory=ProcessSimulationConfig)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProcessDesign(BaseModel):
    """A full design session bundling a process model with optional template and palette."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: ProcessModel
    template: DesignTemplate | None = None
    palette: tuple[PaletteItem, ...] = Field(default_factory=tuple)


__all__ = [
    "DesignElementType",
    "DesignTemplate",
    "PaletteItem",
    "ProcessAnnotation",
    "ProcessConnector",
    "ProcessDesign",
    "ProcessElement",
    "ProcessModel",
    "ProcessSimulationConfig",
    "ProcessSwimLane",
    "ValidationResult",
]
