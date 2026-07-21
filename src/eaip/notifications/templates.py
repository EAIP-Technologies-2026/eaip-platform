"""Template rendering service for notifications."""

from __future__ import annotations

import re
from typing import Any

from eaip.logging.context import get_logger
from eaip.notifications.events import TemplateCreated, TemplateUpdated
from eaip.notifications.exceptions import TemplateNotFoundError
from eaip.notifications.models import NotificationChannel, NotificationTemplate


class TemplateService:
    """Manages notification templates and renders them with variables."""

    def __init__(self) -> None:
        self._templates: dict[str, NotificationTemplate] = {}
        self._log = get_logger("eaip.notifications.templates")
        self._events: list[Any] = []

    def create(
        self,
        template_id: str,
        name: str,
        channel: NotificationChannel,
        subject_template: str,
        body_template: str = "",
        variables: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> NotificationTemplate:
        template = NotificationTemplate(
            id=template_id,
            name=name,
            channel=channel,
            subject_template=subject_template,
            body_template=body_template,
            variables=variables,
            metadata=metadata or {},
        )
        self._templates[template_id] = template
        self._events.append(
            TemplateCreated(template_id=template_id, name=name, channel=channel.value)
        )
        self._log.info("notification.template.created", template_id=template_id)
        return template

    def update(
        self,
        template_id: str,
        *,
        name: str | None = None,
        subject_template: str | None = None,
        body_template: str | None = None,
        variables: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationTemplate:
        existing = self.get(template_id)
        if existing is None:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")

        kwargs: dict[str, Any] = {
            "id": existing.id,
            "name": name if name is not None else existing.name,
            "channel": existing.channel,
            "subject_template": subject_template
            if subject_template is not None
            else existing.subject_template,
            "body_template": body_template if body_template is not None else existing.body_template,
            "variables": variables if variables is not None else existing.variables,
            "metadata": metadata if metadata is not None else existing.metadata,
        }
        template = NotificationTemplate(**kwargs)
        self._templates[template_id] = template
        self._events.append(
            TemplateUpdated(
                template_id=template_id, name=template.name, channel=template.channel.value
            )
        )
        self._log.info("notification.template.updated", template_id=template_id)
        return template

    def get(self, template_id: str) -> NotificationTemplate | None:
        return self._templates.get(template_id)

    def list_templates(self) -> list[NotificationTemplate]:
        return list(self._templates.values())

    def delete(self, template_id: str) -> bool:
        if template_id not in self._templates:
            return False
        del self._templates[template_id]
        self._log.info("notification.template.deleted", template_id=template_id)
        return True

    def render(self, template: NotificationTemplate, variables: dict[str, Any]) -> tuple[str, str]:
        subject = self._render_string(template.subject_template, variables)
        body = (
            self._render_string(template.body_template, variables) if template.body_template else ""
        )
        return subject, body

    def validate(self, template: NotificationTemplate) -> list[str]:
        errors: list[str] = []
        if not template.subject_template:
            errors.append("subject_template is required")
        if not template.name:
            errors.append("name is required")
        if template.variables:
            for var in template.variables:
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", var):
                    errors.append(f"Invalid variable name: '{var}'")
        return errors

    @staticmethod
    def _render_string(template_str: str, variables: dict[str, Any]) -> str:
        def _replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))

        return re.sub(r"\{\{(\w+)\}\}", _replace, template_str)

    def drain_events(self) -> list[Any]:
        events = list(self._events)
        self._events.clear()
        return events


__all__ = ["TemplateService"]
