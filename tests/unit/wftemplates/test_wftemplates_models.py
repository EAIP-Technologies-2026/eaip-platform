"""Tests for Workflow Template models."""

from __future__ import annotations

import pytest

from eaip.wftemplates.models import (
    TemplateSearchFilter,
    TemplateStatus,
    WorkflowTemplate,
    WorkflowTemplateCategory,
)


class TestWorkflowTemplate:
    def test_required_fields(self) -> None:
        tpl = WorkflowTemplate(id="tpl_1", name="Hello World")
        assert tpl.id == "tpl_1"
        assert tpl.name == "Hello World"
        assert tpl.status is TemplateStatus.DRAFT
        assert tpl.tags == ()
        assert tpl.steps == ()
        assert tpl.config == {}

    def test_with_all_fields(self) -> None:
        tpl = WorkflowTemplate(
            id="tpl_2",
            name="Data Pipeline",
            description="A data pipeline template",
            category="etl",
            industry="finance",
            tags=("etl", "finance"),
            steps=({"name": "extract"}, {"name": "transform"}),
            edges=({"from": "extract", "to": "transform"},),
            config={"timeout": 300},
            version="2.0.0",
            rating=4.5,
            download_count=100,
            author="test",
            status=TemplateStatus.PUBLISHED,
            metadata={"source": "marketplace"},
        )
        assert tpl.description == "A data pipeline template"
        assert tpl.rating == 4.5
        assert tpl.download_count == 100
        assert tpl.status is TemplateStatus.PUBLISHED

    def test_frozen(self) -> None:
        tpl = WorkflowTemplate(id="t1", name="test")
        with pytest.raises(ValueError):
            tpl.name = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            WorkflowTemplate(id="t1", name="test", unknown=True)  # type: ignore[call-arg]

    def test_status_default_draft(self) -> None:
        tpl = WorkflowTemplate(id="t1", name="test")
        assert tpl.status is TemplateStatus.DRAFT

    def test_default_values(self) -> None:
        tpl = WorkflowTemplate(id="t1", name="test")
        assert tpl.version == "1.0.0"
        assert tpl.rating == 0.0
        assert tpl.download_count == 0
        assert tpl.author == ""


class TestWorkflowTemplateCategory:
    def test_required_fields(self) -> None:
        cat = WorkflowTemplateCategory(id="cat_1", name="ETL")
        assert cat.id == "cat_1"
        assert cat.name == "ETL"
        assert cat.parent is None
        assert cat.order == 0

    def test_with_all_fields(self) -> None:
        cat = WorkflowTemplateCategory(
            id="cat_2",
            name="Data Science",
            description="Data science workflows",
            icon="chart",
            parent="cat_1",
            order=1,
            metadata={"color": "blue"},
        )
        assert cat.description == "Data science workflows"
        assert cat.parent == "cat_1"
        assert cat.metadata == {"color": "blue"}

    def test_frozen(self) -> None:
        cat = WorkflowTemplateCategory(id="c1", name="test")
        with pytest.raises(ValueError):
            cat.name = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            WorkflowTemplateCategory(id="c1", name="test", unknown=True)  # type: ignore[call-arg]


class TestTemplateSearchFilter:
    def test_defaults(self) -> None:
        filt = TemplateSearchFilter()
        assert filt.sort_by == "download_count"
        assert filt.page == 1
        assert filt.page_size == 20
        assert filt.min_rating == 0.0
        assert filt.tags == ()

    def test_not_frozen(self) -> None:
        filt = TemplateSearchFilter()
        filt.page = 2
        assert filt.page == 2
