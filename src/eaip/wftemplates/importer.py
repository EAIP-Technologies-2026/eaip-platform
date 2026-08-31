"""WorkflowTemplateImporter — imports templates into executable WorkflowDefinitions."""

from __future__ import annotations

from typing import Any

from eaip.wftemplates.events import TemplateImported
from eaip.wftemplates.exceptions import TemplateImportError, TemplateNotFoundError
from eaip.wftemplates.models import TemplateStatus


class WorkflowTemplateImporter:
    def __init__(self, registry: Any = None, event_bus: Any = None) -> None:
        self._registry = registry
        self._event_bus = event_bus

    async def import_template(self, template_id: str) -> dict[str, Any]:
        if self._registry is None:
            raise TemplateImportError(template_id, "no template registry available")
        try:
            tpl = self._registry.get_template(template_id)
        except TemplateNotFoundError:
            raise
        except Exception as exc:
            raise TemplateImportError(template_id, str(exc))

        if tpl.status != TemplateStatus.PUBLISHED:
            raise TemplateImportError(
                template_id, f"template status is {tpl.status.value}, must be published"
            )

        workflow_def = {
            "id": f"wf_{template_id}",
            "name": tpl.name,
            "description": tpl.description,
            "steps": [dict(s) for s in tpl.steps],
            "edges": [dict(e) for e in tpl.edges],
            "config": dict(tpl.config),
            "tags": list(tpl.tags),
            "version": tpl.version,
        }

        self._registry.update_template(template_id, download_count=tpl.download_count + 1)

        if self._event_bus:
            self._event_bus.publish(
                TemplateImported(
                    template_id=template_id,
                    template_name=tpl.name,
                    target_workflow_id=workflow_def["id"],
                )
            )

        return workflow_def


__all__ = ["WorkflowTemplateImporter"]
