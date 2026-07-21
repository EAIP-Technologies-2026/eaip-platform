"""ScaffoldService — project scaffolding from templates with file generation."""

from __future__ import annotations

import os
import time
from typing import Any

from eaip.bootstrap.events import (
    ProjectScaffolded,
    TemplateCreated,
    TemplateDeleted,
    TemplateUpdated,
)
from eaip.bootstrap.exceptions import FileGenerationError, ScaffoldError, TemplateNotFoundError
from eaip.bootstrap.models import ProjectTemplate, ProjectType, ScaffoldConfig, ScaffoldResult


class ScaffoldService:
    def __init__(self, event_bus: Any = None) -> None:
        self._templates: dict[str, ProjectTemplate] = {}
        self._scaffold_results: dict[str, ScaffoldResult] = {}
        self._event_bus = event_bus

    def create_template(self, template: ProjectTemplate) -> ProjectTemplate:
        self._templates[template.id] = template
        if self._event_bus:
            self._event_bus.publish(
                TemplateCreated(
                    template_id=template.id,
                    template_name=template.name,
                    template_type=template.type.value,
                )
            )
        return template

    def get_template(self, template_id: str) -> ProjectTemplate:
        tpl = self._templates.get(template_id)
        if tpl is None:
            raise TemplateNotFoundError(template_id)
        return tpl

    def update_template(self, template_id: str, **updates: Any) -> ProjectTemplate:
        existing = self.get_template(template_id)
        updated = existing.model_copy(update=updates)
        self._templates[template_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                TemplateUpdated(
                    template_id=template_id,
                    template_name=updated.name,
                )
            )
        return updated

    def delete_template(self, template_id: str) -> None:
        tpl = self.get_template(template_id)
        del self._templates[template_id]
        if self._event_bus:
            self._event_bus.publish(
                TemplateDeleted(
                    template_id=template_id,
                    template_name=tpl.name,
                )
            )

    def list_templates(self, type_filter: ProjectType | None = None) -> list[ProjectTemplate]:
        result = list(self._templates.values())
        if type_filter is not None:
            result = [t for t in result if t.type == type_filter]
        return result

    def count_templates(self) -> int:
        return len(self._templates)

    async def render_file(
        self, template: ProjectTemplate, file_path: str, config: ScaffoldConfig
    ) -> str:
        content_parts: list[str] = []
        content_parts.append(f"# {file_path}")
        content_parts.append(f"# Generated from template: {template.name}")
        content_parts.append(f"# Project: {config.project_name}")
        content_parts.append(f"# Author: {config.author}")
        content_parts.append("")
        return "\n".join(content_parts)

    async def create_project_structure(
        self,
        base_path: str,
        files: tuple[str, ...],
        config: ScaffoldConfig,
    ) -> list[str]:
        created: list[str] = []
        for file_path in files:
            full_path = os.path.join(base_path, file_path)
            dir_name = os.path.dirname(full_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            try:
                content = f"# {file_path}\n# Project: {config.project_name}\n"
                with open(full_path, "w") as f:
                    f.write(content)
                created.append(full_path)
            except OSError as exc:
                raise FileGenerationError(file_path, str(exc))
        return created

    async def scaffold(self, template_id: str, config: ScaffoldConfig) -> ScaffoldResult:
        tpl = self.get_template(template_id)
        if tpl.status.value != "active":
            raise ScaffoldError(template_id, f"template status is {tpl.status.value}")

        result_id = f"scaffold_{template_id}_{int(time.monotonic() * 1_000_000)}"
        t0 = time.monotonic()

        package_name = config.package_name or config.project_name.lower().replace("-", "_").replace(
            " ", "_"
        )
        scaffold_config = config.model_copy(update={"package_name": package_name})

        output_base = os.path.join(os.getcwd(), config.project_name)
        try:
            os.makedirs(output_base, exist_ok=True)
            created = await self.create_project_structure(output_base, tpl.files, scaffold_config)
        except FileGenerationError:
            raise
        except OSError as exc:
            raise ScaffoldError(template_id, str(exc))

        duration_ms = (time.monotonic() - t0) * 1000

        result = ScaffoldResult(
            id=result_id,
            template_id=template_id,
            project_name=config.project_name,
            output_path=output_base,
            files_created=len(created),
            duration_ms=round(duration_ms, 2),
        )
        self._scaffold_results[result_id] = result

        if self._event_bus:
            self._event_bus.publish(
                ProjectScaffolded(
                    scaffold_id=result_id,
                    template_id=template_id,
                    project_name=config.project_name,
                    files_created=len(created),
                )
            )

        return result

    async def get_result(self, result_id: str) -> ScaffoldResult | None:
        return self._scaffold_results.get(result_id)


__all__ = ["ScaffoldService"]
