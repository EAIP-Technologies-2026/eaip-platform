"""TemplateEngine — register, render, and manage enterprise templates."""

from __future__ import annotations

import json
from string import Template as StringTemplate

import yaml  # type: ignore[import-untyped]

from eaip.etemplate.events import TemplateRegistered, TemplateRendered, TemplateUpdated
from eaip.etemplate.exceptions import TemplateNotFoundError, TemplateRenderError
from eaip.etemplate.models import (
    RenderResult,
    TemplateDefinition,
    TemplateEngineConfig,
    TemplateFormat,
)
from eaip.logging.context import get_logger


class TemplateEngine:
    def __init__(self, config: TemplateEngineConfig | None = None) -> None:
        self._config = config or TemplateEngineConfig()
        self._templates: dict[str, TemplateDefinition] = {}
        self._log = get_logger("eaip.etemplate.engine")

    @property
    def config(self) -> TemplateEngineConfig:
        return self._config

    async def register_template(self, template: TemplateDefinition) -> TemplateDefinition:
        if len(template.content.encode("utf-8")) > self._config.max_template_size:
            raise TemplateRenderError(
                f"Template content exceeds max size of {self._config.max_template_size} bytes"
            )
        self._templates[template.id] = template
        TemplateRegistered(
            template_id=template.id, name=template.name, format=template.format.value
        )
        self._log.info("etemplate.template.registered", template_id=template.id, name=template.name)
        return template

    async def get_template(self, template_id: str) -> TemplateDefinition:
        template = self._templates.get(template_id)
        if template is None:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        return template

    async def list_templates(self) -> list[TemplateDefinition]:
        return list(self._templates.values())

    async def render_template(
        self, template_id: str, variables: dict[str, str] | None = None
    ) -> RenderResult:
        template = await self.get_template(template_id)
        resolved_vars: dict[str, str] = {}
        vars_dict = variables or {}
        for var in template.variables:
            if var.name in vars_dict:
                resolved_vars[var.name] = vars_dict[var.name]
            elif var.default is not None:
                resolved_vars[var.name] = var.default
            elif var.required:
                raise TemplateRenderError(f"Required variable '{var.name}' not provided")

        content = await self._apply_template(template.content, resolved_vars)
        result = RenderResult(
            content=content,
            format=template.format,
            variables_used=tuple(resolved_vars.keys()),
        )
        TemplateRendered(template_id=template_id, format=template.format.value)
        self._log.info("etemplate.template.rendered", template_id=template_id)
        return result

    async def validate_template(self, template: TemplateDefinition) -> bool:
        try:
            if template.format is TemplateFormat.JSON:
                json.loads(template.content)
            elif template.format is TemplateFormat.YAML:
                yaml.safe_load(template.content)
            elif template.format is TemplateFormat.HTML:
                if not template.content.strip().startswith("<"):
                    return False
            elif template.format is TemplateFormat.CSV:
                lines = template.content.strip().splitlines()
                if not lines:
                    return False
                cols = len(lines[0].split(","))
                for line in lines[1:]:
                    if len(line.split(",")) != cols:
                        return False
            return True
        except (json.JSONDecodeError, yaml.YAMLError):
            return False

    async def update_template(self, template_id: str, **updates: str) -> TemplateDefinition:
        template = await self.get_template(template_id)
        updated = template.model_copy(update=updates, deep=True)
        self._templates[template_id] = updated
        TemplateUpdated(template_id=template_id, changes=updates)
        self._log.info("etemplate.template.updated", template_id=template_id)
        return updated

    async def _apply_template(self, content: str, variables: dict[str, str]) -> str:
        try:
            return StringTemplate(content).safe_substitute(variables)
        except (ValueError, KeyError) as exc:
            raise TemplateRenderError(f"Failed to render template: {exc}") from exc


__all__ = ["TemplateEngine"]
