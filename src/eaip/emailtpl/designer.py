"""EmailTemplateDesigner — create, publish, and render email templates."""

from __future__ import annotations

import re

from eaip.emailtpl.events import TemplateCreated, TemplatePublished, TemplateRendered
from eaip.emailtpl.exceptions import TemplateDesignError, TemplateNotFoundError
from eaip.emailtpl.models import DesignerConfig, EmailTemplate, EmailTemplateRender, TemplateStatus
from eaip.logging.context import get_logger


class EmailTemplateDesigner:
    """Central service for designing and rendering email templates."""

    def __init__(self, config: DesignerConfig | None = None) -> None:
        self._config = config or DesignerConfig()
        self._templates: dict[str, EmailTemplate] = {}
        self._log = get_logger("eaip.emailtpl.designer")

    @property
    def config(self) -> DesignerConfig:
        return self._config

    async def create_template(self, template: EmailTemplate) -> EmailTemplate:
        """Create a new email template."""
        if len(self._templates) >= self._config.max_templates:
            raise TemplateDesignError(
                f"Maximum template limit reached: {self._config.max_templates}"
            )
        self._templates[template.id] = template
        TemplateCreated(
            template_id=template.id,
            name=template.name,
            category=template.category,
        )
        self._log.info("emailtpl.template.created", template_id=template.id, name=template.name)
        return template

    async def get_template(self, template_id: str) -> EmailTemplate:
        """Get an email template by ID."""
        template = self._templates.get(template_id)
        if template is None:
            raise TemplateNotFoundError(f"Email template not found: {template_id}")
        return template

    async def list_templates(
        self, category: str | None = None, status: TemplateStatus | None = None
    ) -> list[EmailTemplate]:
        """List email templates, optionally filtered."""
        result = list(self._templates.values())
        if category is not None:
            result = [t for t in result if t.category == category]
        if status is not None:
            result = [t for t in result if t.status == status]
        return sorted(result, key=lambda t: t.name)

    async def publish_template(self, template_id: str) -> EmailTemplate:
        """Publish a template by setting its status to PUBLISHED."""
        template = self._templates.get(template_id)
        if template is None:
            raise TemplateNotFoundError(f"Email template not found: {template_id}")
        updated = template.model_copy(update={"status": TemplateStatus.PUBLISHED})
        self._templates[template_id] = updated
        TemplatePublished(
            template_id=template_id,
            name=template.name,
            version=template.version,
        )
        self._log.info("emailtpl.template.published", template_id=template_id)
        return updated

    async def render_template(
        self, template_id: str, variables: dict[str, str] | None = None
    ) -> EmailTemplateRender:
        """Render an email template by substituting variables."""
        template = self._templates.get(template_id)
        if template is None:
            raise TemplateNotFoundError(f"Email template not found: {template_id}")

        variables = variables or {}

        def _substitute(text: str) -> str:
            for key, value in variables.items():
                text = re.sub(r"\{\{" + re.escape(key) + r"\}\}", value, text)
            return text

        subject_result = _substitute(template.subject)
        body_result = _substitute(
            template.body_html if self._config.allow_html else template.body_text
        )

        render = EmailTemplateRender(
            template_id=template_id,
            variables=variables,
            subject_result=subject_result,
            body_result=body_result,
        )

        TemplateRendered(template_id=template_id, variable_count=len(variables))
        self._log.info(
            "emailtpl.template.rendered", template_id=template_id, variable_count=len(variables)
        )
        return render

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about email templates."""
        return {
            "total_templates": len(self._templates),
            "draft_templates": sum(
                1 for t in self._templates.values() if t.status == TemplateStatus.DRAFT
            ),
            "published_templates": sum(
                1 for t in self._templates.values() if t.status == TemplateStatus.PUBLISHED
            ),
            "archived_templates": sum(
                1 for t in self._templates.values() if t.status == TemplateStatus.ARCHIVED
            ),
        }


__all__ = ["EmailTemplateDesigner"]
