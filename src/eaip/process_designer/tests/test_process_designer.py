"""Tests for the Process Designer package."""

from __future__ import annotations

import uuid

import pytest

from eaip.process_designer.events import (
    ProcessModelCreated,
)
from eaip.process_designer.exceptions import (
    ConnectorValidationError,
    ElementNotFoundError,
    ProcessDesignError,
    ProcessExportError,
    ProcessImportError,
    ProcessModelNotFoundError,
    ProcessPublishError,
    ProcessSimulationError,
)
from eaip.process_designer.models import (
    DesignElementType,
    DesignTemplate,
    ProcessConnector,
    ProcessElement,
    ProcessModel,
    ProcessSimulationConfig,
)
from eaip.process_designer.service import ProcessDesignerService


@pytest.fixture
def service() -> ProcessDesignerService:
    """Provide a fresh ProcessDesignerService for each test."""
    return ProcessDesignerService()


@pytest.fixture
async def populated_service(service: ProcessDesignerService) -> ProcessDesignerService:
    """Provide a service with a model containing a start and end element."""
    model = await service.create_model("test-model", description="a test model")
    await service.add_element(model.id, DesignElementType.START, label="Start")
    await service.add_element(model.id, DesignElementType.END, label="End")
    return service


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestCRUD:
    """Tests for process model CRUD operations."""

    async def test_create_model(self, service: ProcessDesignerService) -> None:
        """Verify creating a model returns the correct name and description."""
        model = await service.create_model("my-process", description="a process")
        assert model.name == "my-process"
        assert model.description == "a process"
        assert model.version == 1

    async def test_get_model(self, service: ProcessDesignerService) -> None:
        """Verify retrieving a model by ID returns the correct model."""
        model = await service.create_model("get-test")
        retrieved = await service.get_model(model.id)
        assert retrieved.id == model.id
        assert retrieved.name == "get-test"

    async def test_get_model_not_found(self, service: ProcessDesignerService) -> None:
        """Verify getting a nonexistent model raises ProcessModelNotFoundError."""
        with pytest.raises(ProcessModelNotFoundError) as exc:
            await service.get_model("nonexistent")
        assert "nonexistent" in str(exc.value)

    async def test_list_models(self, service: ProcessDesignerService) -> None:
        """Verify listing returns all created models."""
        await service.create_model("a")
        await service.create_model("b")
        models = await service.list_models()
        assert len(models) == 2

    async def test_update_model(self, service: ProcessDesignerService) -> None:
        """Verify updating a model's name works."""
        model = await service.create_model("original")
        updated = await service.update_model(model.id, name="updated")
        assert updated.name == "updated"
        assert updated.id == model.id

    async def test_delete_model(self, service: ProcessDesignerService) -> None:
        """Verify deleting a model removes it from the list."""
        model = await service.create_model("to-delete")
        await service.delete_model(model.id)
        assert len(await service.list_models()) == 0

    async def test_delete_model_not_found(self, service: ProcessDesignerService) -> None:
        """Verify deleting a nonexistent model raises ProcessModelNotFoundError."""
        with pytest.raises(ProcessModelNotFoundError):
            await service.delete_model("nonexistent")


# ---------------------------------------------------------------------------
# Elements
# ---------------------------------------------------------------------------


class TestElements:
    """Tests for adding and removing elements from process models."""

    async def test_add_element(self, service: ProcessDesignerService) -> None:
        """Verify adding an element to a model works."""
        model = await service.create_model("elements")
        updated = await service.add_element(
            model.id, DesignElementType.TASK, label="Do something", position_x=100.0
        )
        assert len(updated.elements) == 1
        elem = updated.elements[0]
        assert elem.type is DesignElementType.TASK
        assert elem.label == "Do something"
        assert elem.position_x == 100.0

    async def test_remove_element(self, populated_service: ProcessDesignerService) -> None:
        """Verify removing an element removes it and cleans up connectors."""
        models = await populated_service.list_models()
        model = models[0]
        elem_id = model.elements[0].id
        updated = await populated_service.remove_element(model.id, elem_id)
        ids = [e.id for e in updated.elements]
        assert elem_id not in ids

    async def test_remove_element_not_found(self, service: ProcessDesignerService) -> None:
        """Verify removing a nonexistent element raises ElementNotFoundError."""
        model = await service.create_model("no-elem")
        with pytest.raises(ElementNotFoundError):
            await service.remove_element(model.id, "missing")

    async def test_add_connector(self, populated_service: ProcessDesignerService) -> None:
        """Verify adding a connector between two elements works."""
        models = await populated_service.list_models()
        model = models[0]
        source = model.elements[0].id
        target = model.elements[1].id
        updated = await populated_service.add_connector(model.id, source, target, label="flow")
        assert len(updated.connectors) == 1
        assert updated.connectors[0].label == "flow"

    async def test_add_connector_invalid_source(self, service: ProcessDesignerService) -> None:
        """Verify adding a connector with invalid source raises ConnectorValidationError."""
        model = await service.create_model("bad-conn")
        with pytest.raises(ConnectorValidationError):
            await service.add_connector(model.id, "bad-src", "bad-tgt")


# ---------------------------------------------------------------------------
# Swimlanes & Annotations
# ---------------------------------------------------------------------------


class TestSwimlanesAndAnnotations:
    """Tests for swimlane and annotation management."""

    async def test_add_swimlane(self, service: ProcessDesignerService) -> None:
        """Verify adding a swimlane to a model works."""
        model = await service.create_model("lanes")
        updated = await service.add_swimlane(model.id, "HR", color="#ff0000")
        assert len(updated.swimlanes) == 1
        assert updated.swimlanes[0].label == "HR"
        assert updated.swimlanes[0].color == "#ff0000"

    async def test_add_annotation(self, service: ProcessDesignerService) -> None:
        """Verify adding an annotation to a model works."""
        model = await service.create_model("annotations")
        updated = await service.add_annotation(model.id, "note text")
        assert len(updated.annotations) == 1
        assert updated.annotations[0].text == "note text"


# ---------------------------------------------------------------------------
# Publish / Version
# ---------------------------------------------------------------------------


class TestPublishAndVersion:
    """Tests for publishing and versioning process models."""

    async def test_publish_model(self, populated_service: ProcessDesignerService) -> None:
        """Verify publishing a valid model sets the published property."""
        models = await populated_service.list_models()
        model = models[0]
        published = await populated_service.publish_model(model.id)
        assert published.properties.get("published") is True

    async def test_publish_invalid_model_fails(self, service: ProcessDesignerService) -> None:
        """Verify publishing an invalid model raises ProcessPublishError."""
        model = await service.create_model("empty")
        with pytest.raises(ProcessPublishError):
            await service.publish_model(model.id)

    async def test_create_version(self, service: ProcessDesignerService) -> None:
        """Verify creating a version increments the version number."""
        model = await service.create_model("ver")
        v2 = await service.create_version(model.id)
        assert v2.version == 2
        v3 = await service.create_version(model.id)
        assert v3.version == 3


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    """Tests for process model validation."""

    async def test_validate_invalid_model(self, service: ProcessDesignerService) -> None:
        """Verify an empty model returns validation errors."""
        model = await service.create_model("invalid")
        result = await service.validate_model(model.id)
        assert not result.is_valid
        assert len(result.errors) > 0

    async def test_validate_valid_model(self, populated_service: ProcessDesignerService) -> None:
        """Verify a model with start and end elements passes validation."""
        models = await populated_service.list_models()
        model = models[0]
        result = await populated_service.validate_model(model.id)
        assert result.is_valid

    async def test_validate_model_no_end_warning(self, service: ProcessDesignerService) -> None:
        """Verify a model with no end element produces a warning."""
        model = await service.create_model("no-end")
        await service.add_element(model.id, DesignElementType.START)
        await service.add_element(model.id, DesignElementType.TASK)
        result = await service.validate_model(model.id)
        assert result.is_valid
        assert any("no end element" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


class TestSimulation:
    """Tests for process simulation."""

    async def test_run_simulation(self, populated_service: ProcessDesignerService) -> None:
        """Verify running simulation on a valid model returns a config with enabled=True."""
        models = await populated_service.list_models()
        model = models[0]
        config = await populated_service.run_simulation(model.id, iterations=500)
        assert config.enabled
        assert config.iterations == 500

    async def test_run_simulation_invalid_model_fails(
        self, service: ProcessDesignerService
    ) -> None:
        """Verify running simulation on an invalid model raises ProcessSimulationError."""
        model = await service.create_model("bad-sim")
        with pytest.raises(ProcessSimulationError):
            await service.run_simulation(model.id)


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------


class TestImportExport:
    """Tests for importing and exporting process models."""

    async def test_export_json(self, populated_service: ProcessDesignerService) -> None:
        """Verify exporting a model to JSON produces a valid string."""
        models = await populated_service.list_models()
        model = models[0]
        exported = await populated_service.export_model(model.id, fmt="json")
        assert isinstance(exported, str)
        assert model.name in exported

    async def test_export_unsupported_format(self, service: ProcessDesignerService) -> None:
        """Verify exporting with an unsupported format raises ProcessExportError."""
        model = await service.create_model("fmt")
        with pytest.raises(ProcessExportError):
            await service.export_model(model.id, fmt="xml")

    async def test_import_json(self, service: ProcessDesignerService) -> None:
        """Verify importing a model from JSON works."""
        model = await service.create_model("import-me")
        data = model.model_dump_json()
        imported = await service.import_model(data, fmt="json")
        assert imported.name == "import-me"
        assert len(await service.list_models()) == 2

    async def test_import_unsupported_format(self, service: ProcessDesignerService) -> None:
        """Verify importing with an unsupported format raises ProcessImportError."""
        with pytest.raises(ProcessImportError):
            await service.import_model("{}", fmt="xml")


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestEvents:
    """Tests for domain event emission."""

    async def test_create_model_emits_event(self) -> None:
        """Verify creating a model emits ProcessModelCreated."""
        events: list[object] = []

        def capture(event: object) -> None:
            events.append(event)

        svc = ProcessDesignerService(event_callback=capture)
        await svc.create_model("event-test")
        assert len(events) == 1
        assert isinstance(events[0], ProcessModelCreated)

    async def test_multiple_operations_emit_events(self) -> None:
        """Verify multiple operations emit the expected events."""
        events: list[object] = []

        def capture(event: object) -> None:
            events.append(event)

        svc = ProcessDesignerService(event_callback=capture)
        model = await svc.create_model("multi-event")
        await svc.add_element(model.id, DesignElementType.START)
        await svc.add_element(model.id, DesignElementType.END)
        models = await svc.list_models()
        m = models[0]
        await svc.add_connector(m.id, m.elements[0].id, m.elements[1].id)
        await svc.validate_model(m.id)
        await svc.publish_model(m.id)
        await svc.create_version(m.id)
        await svc.export_model(m.id)
        await svc.run_simulation(m.id, iterations=100)
        await svc.delete_model(m.id)

        types = {type(e).__name__ for e in events}
        assert "ProcessModelCreated" in types
        assert "ProcessElementAdded" in types
        assert "ProcessConnectorAdded" in types
        assert "ProcessModelValidated" in types
        assert "ProcessModelPublished" in types
        assert "ProcessModelVersionCreated" in types
        assert "ProcessModelExported" in types
        assert "ProcessSimulationCompleted" in types
        assert "ProcessModelDeleted" in types
        assert "ProcessModelUpdated" not in types

    async def test_event_callback_can_be_set_later(self) -> None:
        """Verify the event callback can be set after construction."""
        events: list[object] = []
        svc = ProcessDesignerService()

        def capture(event: object) -> None:
            events.append(event)

        svc.set_event_callback(capture)
        await svc.create_model("lazy-callback")
        assert len(events) == 1

    async def test_event_callback_cleared(self) -> None:
        """Verify clearing the event callback stops event capture."""
        events: list[object] = []
        svc = ProcessDesignerService()

        def capture(event: object) -> None:
            events.append(event)

        svc.set_event_callback(capture)
        await svc.create_model("first")
        svc.set_event_callback(None)
        await svc.create_model("second")
        assert len(events) == 1


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


class TestTemplates:
    """Tests for applying design templates."""

    async def test_apply_template(self, service: ProcessDesignerService) -> None:
        """Verify applying a template merges its elements into the model."""
        model = await service.create_model("template-test")
        template = DesignTemplate(
            id=str(uuid.uuid4()),
            name="simple",
            elements=(
                ProcessElement(
                    id=str(uuid.uuid4()),
                    type=DesignElementType.TASK,
                    label="From template",
                ),
            ),
        )
        updated = await service.apply_template(model.id, template)
        assert len(updated.elements) == 1
        assert updated.elements[0].label == "From template"


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class TestExceptions:
    """Tests for the exception hierarchy."""

    def test_process_design_error_is_base(self) -> None:
        """Verify all designer exceptions inherit from ProcessDesignError."""
        assert issubclass(ProcessModelNotFoundError, ProcessDesignError)
        assert issubclass(ProcessPublishError, ProcessDesignError)
        assert issubclass(ProcessSimulationError, ProcessDesignError)
        assert issubclass(ProcessExportError, ProcessDesignError)
        assert issubclass(ProcessImportError, ProcessDesignError)
        assert issubclass(ElementNotFoundError, ProcessDesignError)
        assert issubclass(ConnectorValidationError, ProcessDesignError)


# ---------------------------------------------------------------------------
# Model immutability & serialization
# ---------------------------------------------------------------------------


class TestModels:
    """Tests for pydantic model constraints and serialization."""

    def test_process_model_frozen(self) -> None:
        """Verify ProcessModel is frozen and cannot be mutated."""
        model = ProcessModel(id="1", name="frozen-test")
        with pytest.raises(AttributeError):
            model.name = "should-not-work"  # type: ignore[misc]

    def test_process_model_extra_forbid(self) -> None:
        """Verify ProcessModel rejects extra fields."""
        with pytest.raises(ValueError):
            ProcessModel(id="1", name="x", unknown_field="bad")  # type: ignore[call-arg]

    def test_simulation_config_defaults(self) -> None:
        """Verify ProcessSimulationConfig has sensible defaults."""
        config = ProcessSimulationConfig()
        assert config.iterations == 1000
        assert config.max_concurrent == 10
        assert config.arrival_rate == 1.0
        assert not config.enabled

    def test_design_element_type_values(self) -> None:
        """Verify DesignElementType enum values."""
        assert DesignElementType.START.value == "start"
        assert DesignElementType.GATEWAY.value == "gateway"

    def test_connector_defaults(self) -> None:
        """Verify ProcessConnector default values."""
        conn = ProcessConnector(id="c1", source_element_id="s1", target_element_id="t1")
        assert conn.priority == 0
        assert not conn.is_default
        assert conn.condition is None

    def test_process_model_deserialization(self) -> None:
        """Verify round-trip serialization of ProcessModel."""
        model = ProcessModel(id="1", name="roundtrip")
        data = model.model_dump_json()
        restored = ProcessModel.model_validate_json(data)
        assert restored.id == model.id
        assert restored.name == model.name
