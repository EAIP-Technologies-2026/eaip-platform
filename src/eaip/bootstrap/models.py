"""Bootstrap models — ProjectTemplate, ScaffoldConfig, ScaffoldResult, BootstrapConfig."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectType(StrEnum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    PLUGIN = "plugin"
    CONNECTOR = "connector"
    API = "api"


class TemplateStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    type: ProjectType
    files: tuple[str, ...] = Field(default_factory=tuple)
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    config_template: dict[str, Any] = Field(default_factory=dict)
    status: TemplateStatus = TemplateStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScaffoldConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_name: str
    package_name: str = ""
    author: str = ""
    description: str = ""
    python_version: str = "3.12"
    include_tests: bool = True
    include_docs: bool = False
    include_ci: bool = False
    include_docker: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScaffoldResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    template_id: str
    project_name: str
    output_path: str = ""
    files_created: int = 0
    duration_ms: float = 0.0
    status: str = "completed"
    metadata: dict[str, Any] = Field(default_factory=dict)


class BootstrapConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_python_version: str = "3.12"
    include_tests_default: bool = True
    include_docs_default: bool = False
    include_ci_default: bool = False
    include_docker_default: bool = False


__all__ = [
    "BootstrapConfig",
    "ProjectTemplate",
    "ProjectType",
    "ScaffoldConfig",
    "ScaffoldResult",
    "TemplateStatus",
]
