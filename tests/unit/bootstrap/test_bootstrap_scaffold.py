"""Tests for ScaffoldService."""

from __future__ import annotations

import os
from typing import Any

import pytest

from eaip.bootstrap.exceptions import TemplateNotFoundError
from eaip.bootstrap.models import ProjectTemplate, ProjectType, ScaffoldConfig
from eaip.bootstrap.scaffold import ScaffoldService


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


class TestScaffoldService:
    @pytest.fixture
    def service(self) -> ScaffoldService:
        return ScaffoldService()

    def test_create_template(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(id="t1", name="Agent", type=ProjectType.AGENT)
        service.create_template(tpl)
        assert service.get_template("t1") == tpl

    def test_get_template_not_found(self, service: ScaffoldService) -> None:
        with pytest.raises(TemplateNotFoundError):
            service.get_template("nonexistent")

    def test_update_template(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(id="t1", name="Original", type=ProjectType.AGENT)
        service.create_template(tpl)
        updated = service.update_template("t1", name="Updated")
        assert updated.name == "Updated"

    def test_delete_template(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(id="t1", name="T", type=ProjectType.AGENT)
        service.create_template(tpl)
        service.delete_template("t1")
        with pytest.raises(TemplateNotFoundError):
            service.get_template("t1")

    def test_delete_template_not_found(self, service: ScaffoldService) -> None:
        with pytest.raises(TemplateNotFoundError):
            service.delete_template("nonexistent")

    def test_list_templates(self, service: ScaffoldService) -> None:
        service.create_template(ProjectTemplate(id="t1", name="A", type=ProjectType.AGENT))
        service.create_template(ProjectTemplate(id="t2", name="B", type=ProjectType.WORKFLOW))
        assert len(service.list_templates()) == 2

    def test_list_templates_filter_by_type(self, service: ScaffoldService) -> None:
        service.create_template(ProjectTemplate(id="t1", name="A", type=ProjectType.AGENT))
        service.create_template(ProjectTemplate(id="t2", name="B", type=ProjectType.WORKFLOW))
        agents = service.list_templates(type_filter=ProjectType.AGENT)
        assert len(agents) == 1
        assert agents[0].id == "t1"

    def test_list_templates_empty(self, service: ScaffoldService) -> None:
        assert service.list_templates() == []

    def test_count_templates(self, service: ScaffoldService) -> None:
        assert service.count_templates() == 0
        service.create_template(ProjectTemplate(id="t1", name="A", type=ProjectType.API))
        assert service.count_templates() == 1

    @pytest.mark.asyncio
    async def test_render_file(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(id="t1", name="Test", type=ProjectType.API)
        config = ScaffoldConfig(project_name="my_proj", author="test")
        content = await service.render_file(tpl, "main.py", config)
        assert "main.py" in content
        assert "Test" in content
        assert "my_proj" in content

    @pytest.mark.asyncio
    async def test_scaffold(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(
            id="t1",
            name="Agent Template",
            type=ProjectType.AGENT,
            files=("main.py", "README.md"),
        )
        service.create_template(tpl)
        config = ScaffoldConfig(project_name="my_agent", author="dev")
        result = await service.scaffold("t1", config)
        assert result.template_id == "t1"
        assert result.project_name == "my_agent"
        assert result.files_created == 2
        assert result.status == "completed"
        assert result.duration_ms > 0

        base_path = os.path.join(os.getcwd(), "my_agent")
        assert os.path.exists(os.path.join(base_path, "main.py"))
        assert os.path.exists(os.path.join(base_path, "README.md"))

        os.remove(os.path.join(base_path, "main.py"))
        os.remove(os.path.join(base_path, "README.md"))
        os.rmdir(base_path)

    @pytest.mark.asyncio
    async def test_scaffold_template_not_found(self, service: ScaffoldService) -> None:
        config = ScaffoldConfig(project_name="test")
        with pytest.raises(TemplateNotFoundError):
            await service.scaffold("nonexistent", config)

    @pytest.mark.asyncio
    async def test_get_result(self, service: ScaffoldService) -> None:
        tpl = ProjectTemplate(id="t1", name="T", type=ProjectType.API, files=("main.py",))
        service.create_template(tpl)
        config = ScaffoldConfig(project_name="test_proj", author="me")
        result = await service.scaffold("t1", config)
        retrieved = await service.get_result(result.id)
        assert retrieved is not None
        assert retrieved.id == result.id

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, service: ScaffoldService) -> None:
        result = await service.get_result("nonexistent")
        assert result is None

    def test_event_publishing_on_create(self) -> None:
        bus = FakeEventBus()
        service = ScaffoldService(event_bus=bus)
        tpl = ProjectTemplate(id="t1", name="Test", type=ProjectType.AGENT)
        service.create_template(tpl)
        assert len(bus.events) == 1
        assert bus.events[0].template_id == "t1"

    def test_event_publishing_on_delete(self) -> None:
        bus = FakeEventBus()
        service = ScaffoldService(event_bus=bus)
        tpl = ProjectTemplate(id="t1", name="Test", type=ProjectType.AGENT)
        service.create_template(tpl)
        service.delete_template("t1")
        assert len(bus.events) == 2
        assert bus.events[1].template_id == "t1"
