"""Domain events for the process designer."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ProcessModelCreated(DomainEvent):
    """Emitted when a new process model is created."""

    event_type: ClassVar[str] = "eaip.process_designer.model_created"

    model_id: str
    name: str


class ProcessModelUpdated(DomainEvent):
    """Emitted when a process model's metadata is updated."""

    event_type: ClassVar[str] = "eaip.process_designer.model_updated"

    model_id: str
    version: int


class ProcessModelDeleted(DomainEvent):
    """Emitted when a process model is deleted."""

    event_type: ClassVar[str] = "eaip.process_designer.model_deleted"

    model_id: str
    name: str


class ProcessModelPublished(DomainEvent):
    """Emitted when a process model is published."""

    event_type: ClassVar[str] = "eaip.process_designer.model_published"

    model_id: str
    name: str
    version: int


class ProcessModelValidated(DomainEvent):
    """Emitted after a process model validation completes."""

    event_type: ClassVar[str] = "eaip.process_designer.model_validated"

    model_id: str
    is_valid: bool
    error_count: int


class ProcessModelVersionCreated(DomainEvent):
    """Emitted when a new version of a process model is created."""

    event_type: ClassVar[str] = "eaip.process_designer.model_version_created"

    model_id: str
    old_version: int
    new_version: int


class ProcessElementAdded(DomainEvent):
    """Emitted when an element is added to a process model."""

    event_type: ClassVar[str] = "eaip.process_designer.element_added"

    model_id: str
    element_id: str
    element_type: str


class ProcessElementRemoved(DomainEvent):
    """Emitted when an element is removed from a process model."""

    event_type: ClassVar[str] = "eaip.process_designer.element_removed"

    model_id: str
    element_id: str


class ProcessConnectorAdded(DomainEvent):
    """Emitted when a connector is added between two elements."""

    event_type: ClassVar[str] = "eaip.process_designer.connector_added"

    model_id: str
    connector_id: str
    source_element_id: str
    target_element_id: str


class ProcessModelImported(DomainEvent):
    """Emitted when a process model is imported from an external format."""

    event_type: ClassVar[str] = "eaip.process_designer.model_imported"

    model_id: str
    format: str


class ProcessModelExported(DomainEvent):
    """Emitted when a process model is exported to an external format."""

    event_type: ClassVar[str] = "eaip.process_designer.model_exported"

    model_id: str
    format: str


class ProcessSimulationCompleted(DomainEvent):
    """Emitted when a process simulation finishes."""

    event_type: ClassVar[str] = "eaip.process_designer.simulation_completed"

    model_id: str
    iterations: int
    avg_completion_time: float


__all__ = [
    "ProcessConnectorAdded",
    "ProcessElementAdded",
    "ProcessElementRemoved",
    "ProcessModelCreated",
    "ProcessModelDeleted",
    "ProcessModelExported",
    "ProcessModelImported",
    "ProcessModelPublished",
    "ProcessModelUpdated",
    "ProcessModelValidated",
    "ProcessModelVersionCreated",
    "ProcessSimulationCompleted",
]
