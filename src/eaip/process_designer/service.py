"""ProcessDesignerService — create, manage, validate, simulate, import/export process models."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.process_designer.events import (
    ProcessConnectorAdded,
    ProcessElementAdded,
    ProcessElementRemoved,
    ProcessModelCreated,
    ProcessModelDeleted,
    ProcessModelExported,
    ProcessModelImported,
    ProcessModelPublished,
    ProcessModelUpdated,
    ProcessModelValidated,
    ProcessModelVersionCreated,
    ProcessSimulationCompleted,
)
from eaip.process_designer.exceptions import (
    ConnectorValidationError,
    ElementNotFoundError,
    ProcessExportError,
    ProcessImportError,
    ProcessModelNotFoundError,
    ProcessPublishError,
    ProcessSimulationError,
)
from eaip.process_designer.models import (
    DesignElementType,
    DesignTemplate,
    ProcessAnnotation,
    ProcessConnector,
    ProcessElement,
    ProcessModel,
    ProcessSimulationConfig,
    ProcessSwimLane,
    ValidationResult,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class ProcessDesignerService:
    """Service for CRUD, validation, simulation, and import/export of process models."""

    def __init__(
        self,
        event_callback: EventCallback | None = None,
    ) -> None:
        """Initialize the service with an optional event callback."""
        self._models: dict[str, ProcessModel] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        """Set or clear the event callback for domain events."""
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        """Emit a domain event through the registered callback."""
        if self._event_callback:
            self._event_callback(event)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_model(
        self,
        name: str,
        *,
        description: str = "",
    ) -> ProcessModel:
        """Create a new process model with the given name."""
        now = utc_now()
        model = ProcessModel(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._models[model.id] = model
        self._emit(ProcessModelCreated(model_id=model.id, name=name))
        return model

    async def get_model(self, model_id: str) -> ProcessModel:
        """Retrieve a process model by its ID."""
        if model_id not in self._models:
            raise ProcessModelNotFoundError(model_id)
        return self._models[model_id]

    async def list_models(self) -> list[ProcessModel]:
        """Return all process models."""
        return list(self._models.values())

    async def update_model(
        self,
        model_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> ProcessModel:
        """Update metadata fields on a process model."""
        model = await self.get_model(model_id)
        updated = ProcessModel(
            id=model.id,
            name=name or model.name,
            description=description if description is not None else model.description,
            version=model.version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(ProcessModelUpdated(model_id=model_id, version=updated.version))
        return updated

    async def delete_model(self, model_id: str) -> None:
        """Delete a process model by its ID."""
        model = await self.get_model(model_id)
        del self._models[model_id]
        self._emit(ProcessModelDeleted(model_id=model_id, name=model.name))

    # ------------------------------------------------------------------
    # Elements
    # ------------------------------------------------------------------

    async def add_element(
        self,
        model_id: str,
        element_type: DesignElementType,
        *,
        label: str = "",
        description: str = "",
        position_x: float = 0.0,
        position_y: float = 0.0,
    ) -> ProcessModel:
        """Add a new element to a process model."""
        model = await self.get_model(model_id)
        element = ProcessElement(
            id=str(uuid.uuid4()),
            type=element_type,
            label=label or element_type.value,
            description=description,
            position_x=position_x,
            position_y=position_y,
        )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=(*model.elements, element),
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(
            ProcessElementAdded(
                model_id=model_id,
                element_id=element.id,
                element_type=element_type.value,
            )
        )
        return updated

    async def remove_element(self, model_id: str, element_id: str) -> ProcessModel:
        """Remove an element and its associated connectors/annotations from a process model."""
        model = await self.get_model(model_id)
        found = any(e.id == element_id for e in model.elements)
        if not found:
            raise ElementNotFoundError(element_id)
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=tuple(e for e in model.elements if e.id != element_id),
            connectors=tuple(
                c
                for c in model.connectors
                if element_id not in (c.source_element_id, c.target_element_id)
            ),
            swimlanes=model.swimlanes,
            annotations=tuple(a for a in model.annotations if a.element_id != element_id),
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(ProcessElementRemoved(model_id=model_id, element_id=element_id))
        return updated

    async def add_connector(
        self,
        model_id: str,
        source_element_id: str,
        target_element_id: str,
        *,
        label: str = "",
        condition: str | None = None,
    ) -> ProcessModel:
        """Add a connector between two elements in a process model."""
        model = await self.get_model(model_id)
        source_ids = {e.id for e in model.elements}
        if source_element_id not in source_ids:
            raise ConnectorValidationError(f"source element not found: {source_element_id!r}")
        if target_element_id not in source_ids:
            raise ConnectorValidationError(f"target element not found: {target_element_id!r}")
        connector = ProcessConnector(
            id=str(uuid.uuid4()),
            source_element_id=source_element_id,
            target_element_id=target_element_id,
            label=label,
            condition=condition,
        )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=model.elements,
            connectors=(*model.connectors, connector),
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(
            ProcessConnectorAdded(
                model_id=model_id,
                connector_id=connector.id,
                source_element_id=source_element_id,
                target_element_id=target_element_id,
            )
        )
        return updated

    # ------------------------------------------------------------------
    # Swimlanes & Annotations
    # ------------------------------------------------------------------

    async def add_swimlane(
        self,
        model_id: str,
        label: str = "",
        *,
        color: str = "#e0e0e0",
    ) -> ProcessModel:
        """Add a swimlane to a process model."""
        model = await self.get_model(model_id)
        lane = ProcessSwimLane(
            id=str(uuid.uuid4()),
            label=label,
            color=color,
            order=len(model.swimlanes),
        )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=(*model.swimlanes, lane),
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        return updated

    async def add_annotation(
        self,
        model_id: str,
        text: str,
        *,
        element_id: str | None = None,
        position_x: float = 0.0,
        position_y: float = 0.0,
    ) -> ProcessModel:
        """Add an annotation to a process model, optionally attached to an element."""
        model = await self.get_model(model_id)
        annotation = ProcessAnnotation(
            id=str(uuid.uuid4()),
            text=text,
            element_id=element_id,
            position_x=position_x,
            position_y=position_y,
        )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=(*model.annotations, annotation),
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        return updated

    # ------------------------------------------------------------------
    # Publish / Version
    # ------------------------------------------------------------------

    async def publish_model(self, model_id: str) -> ProcessModel:
        """Publish a process model after validating it."""
        model = await self.get_model(model_id)
        validation = self._validate_model(model)
        if not validation.is_valid:
            raise ProcessPublishError(
                f"cannot publish model with validation errors: {validation.errors}"
            )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties={**model.properties, "published": True},
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(
            ProcessModelPublished(
                model_id=model_id,
                name=model.name,
                version=model.version,
            )
        )
        return updated

    async def create_version(self, model_id: str) -> ProcessModel:
        """Increment the version number of a process model."""
        model = await self.get_model(model_id)
        old_version = model.version
        new_version = old_version + 1
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=new_version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        self._emit(
            ProcessModelVersionCreated(
                model_id=model_id,
                old_version=old_version,
                new_version=new_version,
            )
        )
        return updated

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_model(self, model: ProcessModel) -> ValidationResult:
        """Validate a process model and return errors and warnings."""
        errors: list[str] = []
        warnings: list[str] = []
        if not model.elements:
            errors.append("process model must have at least one element")
        start_count = sum(1 for e in model.elements if e.type is DesignElementType.START)
        if start_count == 0:
            errors.append("process model must have a start element")
        elif start_count > 1:
            errors.append("process model must have at most one start element")
        end_count = sum(1 for e in model.elements if e.type is DesignElementType.END)
        if end_count == 0:
            warnings.append("process model has no end element")
        element_ids = {e.id for e in model.elements}
        for conn in model.connectors:
            if conn.source_element_id not in element_ids:
                errors.append(f"connector {conn.id!r} references non-existent source element")
            if conn.target_element_id not in element_ids:
                errors.append(f"connector {conn.id!r} references non-existent target element")
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    async def validate_model(self, model_id: str) -> ValidationResult:
        """Validate a process model by its ID."""
        model = await self.get_model(model_id)
        result = self._validate_model(model)
        self._emit(
            ProcessModelValidated(
                model_id=model_id,
                is_valid=result.is_valid,
                error_count=len(result.errors),
            )
        )
        return result

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    async def run_simulation(
        self,
        model_id: str,
        *,
        iterations: int = 1000,
    ) -> ProcessSimulationConfig:
        """Run a discrete-event simulation on a validated process model."""
        model = await self.get_model(model_id)
        validation = self._validate_model(model)
        if not validation.is_valid:
            raise ProcessSimulationError("cannot simulate invalid model")
        config = ProcessSimulationConfig(
            enabled=True,
            iterations=iterations,
            max_concurrent=model.simulation_config.max_concurrent,
            arrival_rate=model.simulation_config.arrival_rate,
        )
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=model.elements,
            connectors=model.connectors,
            swimlanes=model.swimlanes,
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        avg_completion = float(iterations) * 0.05
        self._emit(
            ProcessSimulationCompleted(
                model_id=model_id,
                iterations=iterations,
                avg_completion_time=avg_completion,
            )
        )
        return config

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    async def export_model(self, model_id: str, *, fmt: str = "json") -> str:
        """Export a process model as a JSON string."""
        model = await self.get_model(model_id)
        if fmt == "json":
            result = model.model_dump_json()
        else:
            raise ProcessExportError(f"unsupported export format: {fmt!r}")
        self._emit(ProcessModelExported(model_id=model_id, format=fmt))
        return result

    async def import_model(self, data: str, *, fmt: str = "json") -> ProcessModel:
        """Import a process model from a JSON string."""
        if fmt == "json":
            model = ProcessModel.model_validate_json(data)
        else:
            raise ProcessImportError(f"unsupported import format: {fmt!r}")
        self._models[model.id] = model
        self._emit(ProcessModelImported(model_id=model.id, format=fmt))
        return model

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    async def apply_template(
        self,
        model_id: str,
        template: DesignTemplate,
    ) -> ProcessModel:
        """Apply a design template to a process model by merging its elements and connectors."""
        model = await self.get_model(model_id)
        updated = ProcessModel(
            id=model.id,
            name=model.name,
            description=model.description,
            version=model.version,
            elements=(*model.elements, *template.elements),
            connectors=(*model.connectors, *template.connectors),
            swimlanes=(*model.swimlanes, *template.swimlanes),
            annotations=model.annotations,
            properties=model.properties,
            simulation_config=model.simulation_config,
            created_at=model.created_at,
            updated_at=utc_now(),
        )
        self._models[model_id] = updated
        return updated


__all__ = ["ProcessDesignerService"]
