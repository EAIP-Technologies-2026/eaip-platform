"""Tests for Bootstrap models."""

from __future__ import annotations

import pytest

from eaip.bootstrap.models import (
    BootstrapConfig,
    ProjectTemplate,
    ProjectType,
    ScaffoldConfig,
    ScaffoldResult,
    TemplateStatus,
)


class TestProjectTemplate:
    def test_required_fields(self) -> None:
        tpl = ProjectTemplate(id="tpl_1", name="Agent Template", type=ProjectType.AGENT)
        assert tpl.id == "tpl_1"
        assert tpl.name == "Agent Template"
        assert tpl.type is ProjectType.AGENT
        assert tpl.status is TemplateStatus.ACTIVE

    def test_with_all_fields(self) -> None:
        tpl = ProjectTemplate(
            id="tpl_2",
            name="Workflow Template",
            description="A workflow scaffold",
            type=ProjectType.WORKFLOW,
            files=("main.py", "config.yaml"),
            dependencies=("eaip", "pydantic"),
            config_template={"version": "1"},
            status=TemplateStatus.INACTIVE,
            metadata={"author": "test"},
        )
        assert tpl.files == ("main.py", "config.yaml")
        assert tpl.status is TemplateStatus.INACTIVE

    def test_frozen(self) -> None:
        tpl = ProjectTemplate(id="t1", name="T", type=ProjectType.PLUGIN)
        with pytest.raises(ValueError):
            tpl.name = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ProjectTemplate(id="t1", name="T", type=ProjectType.API, unknown=True)  # type: ignore[call-arg]

    def test_project_type_values(self) -> None:
        assert ProjectType.AGENT.value == "agent"
        assert ProjectType.WORKFLOW.value == "workflow"
        assert ProjectType.PLUGIN.value == "plugin"
        assert ProjectType.CONNECTOR.value == "connector"
        assert ProjectType.API.value == "api"


class TestScaffoldConfig:
    def test_required_fields(self) -> None:
        cfg = ScaffoldConfig(project_name="my_project")
        assert cfg.project_name == "my_project"
        assert cfg.python_version == "3.12"
        assert cfg.include_tests is True
        assert cfg.include_docs is False

    def test_frozen(self) -> None:
        cfg = ScaffoldConfig(project_name="test")
        with pytest.raises(ValueError):
            cfg.project_name = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ScaffoldConfig(project_name="test", unknown=True)  # type: ignore[call-arg]


class TestScaffoldResult:
    def test_required_fields(self) -> None:
        result = ScaffoldResult(id="r1", template_id="t1", project_name="test")
        assert result.status == "completed"
        assert result.files_created == 0

    def test_frozen(self) -> None:
        result = ScaffoldResult(id="r1", template_id="t1", project_name="test")
        with pytest.raises(ValueError):
            result.status = "failed"


class TestBootstrapConfig:
    def test_defaults(self) -> None:
        cfg = BootstrapConfig()
        assert cfg.default_python_version == "3.12"
        assert cfg.include_tests_default is True
        assert cfg.include_docs_default is False

    def test_custom_values(self) -> None:
        cfg = BootstrapConfig(
            default_python_version="3.11",
            include_tests_default=False,
            include_ci_default=True,
        )
        assert cfg.default_python_version == "3.11"
        assert cfg.include_tests_default is False
        assert cfg.include_ci_default is True

    def test_frozen(self) -> None:
        cfg = BootstrapConfig()
        with pytest.raises(ValueError):
            cfg.default_python_version = "3.10"
