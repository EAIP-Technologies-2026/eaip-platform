"""Tests for WorkflowTemplateRegistry."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.wftemplates.exceptions import CategoryNotFoundError, TemplateNotFoundError
from eaip.wftemplates.models import (
    TemplateSearchFilter,
    TemplateStatus,
    WorkflowTemplate,
    WorkflowTemplateCategory,
)
from eaip.wftemplates.registry import WorkflowTemplateRegistry


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


class TestWorkflowTemplateRegistry:
    def test_create_and_get_template(self) -> None:
        reg = WorkflowTemplateRegistry()
        tpl = WorkflowTemplate(id="t1", name="Template 1")
        reg.create_template(tpl)
        assert reg.get_template("t1") == tpl

    def test_get_template_not_found(self) -> None:
        reg = WorkflowTemplateRegistry()
        with pytest.raises(TemplateNotFoundError):
            reg.get_template("nonexistent")

    def test_update_template(self) -> None:
        reg = WorkflowTemplateRegistry()
        tpl = WorkflowTemplate(id="t1", name="Original")
        reg.create_template(tpl)
        updated = reg.update_template("t1", name="Updated", description="new desc")
        assert updated.name == "Updated"
        assert updated.description == "new desc"
        assert reg.get_template("t1").name == "Updated"

    def test_update_template_not_found(self) -> None:
        reg = WorkflowTemplateRegistry()
        with pytest.raises(TemplateNotFoundError):
            reg.update_template("nonexistent", name="test")

    def test_delete_template(self) -> None:
        reg = WorkflowTemplateRegistry()
        tpl = WorkflowTemplate(id="t1", name="Test")
        reg.create_template(tpl)
        reg.delete_template("t1")
        with pytest.raises(TemplateNotFoundError):
            reg.get_template("t1")

    def test_delete_template_not_found(self) -> None:
        reg = WorkflowTemplateRegistry()
        with pytest.raises(TemplateNotFoundError):
            reg.delete_template("nonexistent")

    def test_list_templates(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(WorkflowTemplate(id="t1", name="A"))
        reg.create_template(WorkflowTemplate(id="t2", name="B"))
        assert len(reg.list_templates()) == 2

    def test_list_templates_empty(self) -> None:
        reg = WorkflowTemplateRegistry()
        assert reg.list_templates() == []

    def test_list_templates_filter_by_status(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(WorkflowTemplate(id="t1", name="A", status=TemplateStatus.PUBLISHED))
        reg.create_template(WorkflowTemplate(id="t2", name="B", status=TemplateStatus.DRAFT))
        published = reg.list_templates(status=TemplateStatus.PUBLISHED)
        assert len(published) == 1
        assert published[0].id == "t1"

    def test_publish(self) -> None:
        reg = WorkflowTemplateRegistry()
        tpl = WorkflowTemplate(id="t1", name="Test")
        reg.create_template(tpl)
        published = reg.publish("t1")
        assert published.status is TemplateStatus.PUBLISHED
        assert reg.get_template("t1").status is TemplateStatus.PUBLISHED

    def test_archive(self) -> None:
        reg = WorkflowTemplateRegistry()
        tpl = WorkflowTemplate(id="t1", name="Test")
        reg.create_template(tpl)
        archived = reg.archive("t1")
        assert archived.status is TemplateStatus.ARCHIVED

    def test_list_by_category(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(id="t1", name="A", category="etl", status=TemplateStatus.PUBLISHED)
        )
        reg.create_template(
            WorkflowTemplate(id="t2", name="B", category="etl", status=TemplateStatus.DRAFT)
        )
        reg.create_template(
            WorkflowTemplate(id="t3", name="C", category="ml", status=TemplateStatus.PUBLISHED)
        )
        etl_templates = reg.list_by_category("etl")
        assert len(etl_templates) == 1
        assert etl_templates[0].id == "t1"

    def test_search_with_filters(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(
                id="t1",
                name="Pipe",
                category="etl",
                industry="finance",
                tags=("etl",),
                status=TemplateStatus.PUBLISHED,
                download_count=10,
            )
        )
        reg.create_template(
            WorkflowTemplate(
                id="t2",
                name="Train",
                category="ml",
                industry="tech",
                tags=("ml",),
                status=TemplateStatus.PUBLISHED,
                download_count=20,
            )
        )
        filter_obj = TemplateSearchFilter(category="etl", page=1, page_size=10)
        results = reg.search(filter_obj)
        assert len(results) == 1
        assert results[0].id == "t1"

    def test_search_by_tags(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(
                id="t1",
                name="A",
                tags=("etl", "finance"),
                status=TemplateStatus.PUBLISHED,
            )
        )
        reg.create_template(
            WorkflowTemplate(
                id="t2",
                name="B",
                tags=("ml",),
                status=TemplateStatus.PUBLISHED,
            )
        )
        filter_obj = TemplateSearchFilter(tags=("etl",))
        results = reg.search(filter_obj)
        assert len(results) == 1
        assert results[0].id == "t1"

    def test_search_empty_result(self) -> None:
        reg = WorkflowTemplateRegistry()
        filter_obj = TemplateSearchFilter(category="nonexistent")
        results = reg.search(filter_obj)
        assert results == []

    def test_list_popular(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(
                id="t1",
                name="A",
                status=TemplateStatus.PUBLISHED,
                download_count=5,
            )
        )
        reg.create_template(
            WorkflowTemplate(
                id="t2",
                name="B",
                status=TemplateStatus.PUBLISHED,
                download_count=10,
            )
        )
        popular = reg.list_popular()
        assert popular[0].id == "t2"

    def test_list_popular_empty(self) -> None:
        reg = WorkflowTemplateRegistry()
        assert reg.list_popular() == []

    def test_list_recent(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(WorkflowTemplate(id="t1", name="A", status=TemplateStatus.PUBLISHED))
        reg.create_template(WorkflowTemplate(id="t2", name="B", status=TemplateStatus.PUBLISHED))
        recent = reg.list_recent()
        assert len(recent) == 2

    def test_get_related(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(
                id="t1", name="A", tags=("etl", "finance"), status=TemplateStatus.PUBLISHED
            )
        )
        reg.create_template(
            WorkflowTemplate(id="t2", name="B", tags=("etl",), status=TemplateStatus.PUBLISHED)
        )
        reg.create_template(
            WorkflowTemplate(id="t3", name="C", tags=("ml",), status=TemplateStatus.PUBLISHED)
        )
        related = reg.get_related("t1")
        assert len(related) == 1
        assert related[0].id == "t2"

    def test_get_related_no_matches(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_template(
            WorkflowTemplate(id="t1", name="A", tags=("etl",), status=TemplateStatus.PUBLISHED)
        )
        reg.create_template(
            WorkflowTemplate(id="t2", name="B", tags=("ml",), status=TemplateStatus.PUBLISHED)
        )
        related = reg.get_related("t1")
        assert related == []

    def test_category_crud(self) -> None:
        reg = WorkflowTemplateRegistry()
        cat = WorkflowTemplateCategory(id="c1", name="ETL")
        reg.create_category(cat)
        assert reg.get_category("c1") == cat
        updated = reg.update_category("c1", name="Data ETL")
        assert updated.name == "Data ETL"

    def test_get_category_not_found(self) -> None:
        reg = WorkflowTemplateRegistry()
        with pytest.raises(CategoryNotFoundError):
            reg.get_category("nonexistent")

    def test_list_categories(self) -> None:
        reg = WorkflowTemplateRegistry()
        reg.create_category(WorkflowTemplateCategory(id="c2", name="ML", order=2))
        reg.create_category(WorkflowTemplateCategory(id="c1", name="ETL", order=1))
        cats = reg.list_categories()
        assert len(cats) == 2
        assert cats[0].id == "c1"
        assert cats[1].id == "c2"

    def test_event_publishing(self) -> None:
        bus = FakeEventBus()
        reg = WorkflowTemplateRegistry(event_bus=bus)
        tpl = WorkflowTemplate(id="t1", name="Test")
        reg.create_template(tpl)
        assert len(bus.events) == 1
        from eaip.wftemplates.events import TemplateCreated

        assert isinstance(bus.events[0], TemplateCreated)

        reg.publish("t1")
        assert len(bus.events) == 2

        reg.archive("t1")
        assert len(bus.events) == 3

    def test_count_templates(self) -> None:
        reg = WorkflowTemplateRegistry()
        assert reg.count_templates() == 0
        reg.create_template(WorkflowTemplate(id="t1", name="A"))
        assert reg.count_templates() == 1

    def test_count_categories(self) -> None:
        reg = WorkflowTemplateRegistry()
        assert reg.count_categories() == 0
        reg.create_category(WorkflowTemplateCategory(id="c1", name="C"))
        assert reg.count_categories() == 1
