"""Tests for WorkflowTemplateImporter."""

from __future__ import annotations

import pytest

from eaip.wftemplates.exceptions import TemplateImportError, TemplateNotFoundError
from eaip.wftemplates.importer import WorkflowTemplateImporter
from eaip.wftemplates.models import TemplateStatus, WorkflowTemplate
from eaip.wftemplates.registry import WorkflowTemplateRegistry


class TestWorkflowTemplateImporter:
    @pytest.fixture
    def registry(self) -> WorkflowTemplateRegistry:
        return WorkflowTemplateRegistry()

    @pytest.fixture
    def importer(self, registry: WorkflowTemplateRegistry) -> WorkflowTemplateImporter:
        return WorkflowTemplateImporter(registry=registry)

    @pytest.mark.asyncio
    async def test_import_published_template(
        self, importer: WorkflowTemplateImporter, registry: WorkflowTemplateRegistry
    ) -> None:
        tpl = WorkflowTemplate(
            id="t1",
            name="Data Pipe",
            description="A pipeline",
            steps=({"name": "extract"},),
            edges=({"from": "start", "to": "end"},),
            config={"timeout": 60},
            tags=("etl",),
            status=TemplateStatus.PUBLISHED,
        )
        registry.create_template(tpl)
        result = await importer.import_template("t1")
        assert result["id"] == "wf_t1"
        assert result["name"] == "Data Pipe"
        assert len(result["steps"]) == 1
        assert result["config"]["timeout"] == 60

    @pytest.mark.asyncio
    async def test_import_draft_template_raises_error(
        self, importer: WorkflowTemplateImporter, registry: WorkflowTemplateRegistry
    ) -> None:
        tpl = WorkflowTemplate(id="t2", name="Draft", status=TemplateStatus.DRAFT)
        registry.create_template(tpl)
        with pytest.raises(TemplateImportError, match="must be published"):
            await importer.import_template("t2")

    @pytest.mark.asyncio
    async def test_import_archived_template_raises_error(
        self, importer: WorkflowTemplateImporter, registry: WorkflowTemplateRegistry
    ) -> None:
        tpl = WorkflowTemplate(id="t3", name="Archived", status=TemplateStatus.ARCHIVED)
        registry.create_template(tpl)
        with pytest.raises(TemplateImportError, match="must be published"):
            await importer.import_template("t3")

    @pytest.mark.asyncio
    async def test_import_nonexistent_template(self, importer: WorkflowTemplateImporter) -> None:
        with pytest.raises(TemplateNotFoundError):
            await importer.import_template("nonexistent")

    @pytest.mark.asyncio
    async def test_import_no_registry(self) -> None:
        importer = WorkflowTemplateImporter()
        with pytest.raises(TemplateImportError):
            await importer.import_template("t1")

    @pytest.mark.asyncio
    async def test_import_increments_download_count(
        self, importer: WorkflowTemplateImporter, registry: WorkflowTemplateRegistry
    ) -> None:
        tpl = WorkflowTemplate(
            id="t1", name="Test", status=TemplateStatus.PUBLISHED, download_count=5
        )
        registry.create_template(tpl)
        await importer.import_template("t1")
        assert registry.get_template("t1").download_count == 6

    @pytest.mark.asyncio
    async def test_import_returns_workflow_definition_structure(
        self, importer: WorkflowTemplateImporter, registry: WorkflowTemplateRegistry
    ) -> None:
        tpl = WorkflowTemplate(
            id="t1",
            name="Pipe",
            description="desc",
            steps=({"step1": "a"},),
            edges=({"edge1": "b"},),
            config={"key": "val"},
            tags=("t1",),
            version="1.0.0",
            status=TemplateStatus.PUBLISHED,
        )
        registry.create_template(tpl)
        result = await importer.import_template("t1")
        assert "id" in result
        assert "name" in result
        assert "steps" in result
        assert "edges" in result
        assert "config" in result
        assert "tags" in result
        assert "version" in result
