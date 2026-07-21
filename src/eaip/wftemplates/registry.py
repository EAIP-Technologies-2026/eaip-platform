"""WorkflowTemplateRegistry — CRUD, search, publish, archive for templates and categories."""

from __future__ import annotations

from typing import Any

from eaip.wftemplates.events import (
    CategoryCreated,
    CategoryUpdated,
    TemplateArchived,
    TemplateCreated,
    TemplatePublished,
)
from eaip.wftemplates.exceptions import CategoryNotFoundError, TemplateNotFoundError
from eaip.wftemplates.models import (
    TemplateSearchFilter,
    TemplateStatus,
    WorkflowTemplate,
    WorkflowTemplateCategory,
)


class WorkflowTemplateRegistry:
    def __init__(self, event_bus: Any = None) -> None:
        self._templates: dict[str, WorkflowTemplate] = {}
        self._categories: dict[str, WorkflowTemplateCategory] = {}
        self._event_bus = event_bus

    def create_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        self._templates[template.id] = template
        if self._event_bus:
            self._event_bus.publish(
                TemplateCreated(
                    template_id=template.id,
                    template_name=template.name,
                    category=template.category,
                )
            )
        return template

    def get_template(self, template_id: str) -> WorkflowTemplate:
        tpl = self._templates.get(template_id)
        if tpl is None:
            raise TemplateNotFoundError(template_id)
        return tpl

    def update_template(self, template_id: str, **updates: Any) -> WorkflowTemplate:
        existing = self.get_template(template_id)
        updated = existing.model_copy(update=updates)
        self._templates[template_id] = updated
        return updated

    def delete_template(self, template_id: str) -> None:
        if template_id not in self._templates:
            raise TemplateNotFoundError(template_id)
        del self._templates[template_id]

    def list_templates(self, status: TemplateStatus | None = None) -> list[WorkflowTemplate]:
        result = list(self._templates.values())
        if status is not None:
            result = [t for t in result if t.status == status]
        return result

    def publish(self, template_id: str) -> WorkflowTemplate:
        existing = self.get_template(template_id)
        updated = existing.model_copy(update={"status": TemplateStatus.PUBLISHED})
        self._templates[template_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                TemplatePublished(
                    template_id=template_id,
                    template_name=updated.name,
                    version=updated.version,
                )
            )
        return updated

    def archive(self, template_id: str) -> WorkflowTemplate:
        existing = self.get_template(template_id)
        updated = existing.model_copy(update={"status": TemplateStatus.ARCHIVED})
        self._templates[template_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                TemplateArchived(
                    template_id=template_id,
                    template_name=updated.name,
                )
            )
        return updated

    def list_by_category(self, category: str) -> list[WorkflowTemplate]:
        return [
            t
            for t in self._templates.values()
            if t.category == category and t.status == TemplateStatus.PUBLISHED
        ]

    def search(self, filter_obj: TemplateSearchFilter) -> list[WorkflowTemplate]:
        result = [t for t in self._templates.values() if t.status == TemplateStatus.PUBLISHED]
        if filter_obj.category:
            result = [t for t in result if t.category == filter_obj.category]
        if filter_obj.tags:
            filter_tags = set(filter_obj.tags)
            result = [t for t in result if filter_tags.intersection(t.tags)]
        if filter_obj.industry:
            result = [t for t in result if t.industry == filter_obj.industry]
        if filter_obj.min_rating > 0:
            result = [t for t in result if t.rating >= filter_obj.min_rating]

        if filter_obj.sort_by == "name":
            result.sort(key=lambda t: t.name)
        elif filter_obj.sort_by == "rating":
            result.sort(key=lambda t: t.rating, reverse=True)
        else:
            result.sort(key=lambda t: t.download_count, reverse=True)

        start = (filter_obj.page - 1) * filter_obj.page_size
        return result[start : start + filter_obj.page_size]

    def list_popular(self, limit: int = 10) -> list[WorkflowTemplate]:
        published = [t for t in self._templates.values() if t.status == TemplateStatus.PUBLISHED]
        published.sort(key=lambda t: t.download_count, reverse=True)
        return published[:limit]

    def list_recent(self, limit: int = 10) -> list[WorkflowTemplate]:
        published = [t for t in self._templates.values() if t.status == TemplateStatus.PUBLISHED]
        return published[-limit:][::-1]

    def get_related(self, template_id: str, limit: int = 5) -> list[WorkflowTemplate]:
        tpl = self.get_template(template_id)
        tpl_tags = set(tpl.tags)
        related = [
            t
            for t in self._templates.values()
            if t.id != template_id
            and t.status == TemplateStatus.PUBLISHED
            and tpl_tags.intersection(t.tags)
        ]
        related.sort(key=lambda t: len(tpl_tags.intersection(t.tags)), reverse=True)
        return related[:limit]

    def create_category(self, category: WorkflowTemplateCategory) -> WorkflowTemplateCategory:
        self._categories[category.id] = category
        if self._event_bus:
            self._event_bus.publish(
                CategoryCreated(
                    category_id=category.id,
                    category_name=category.name,
                )
            )
        return category

    def get_category(self, category_id: str) -> WorkflowTemplateCategory:
        cat = self._categories.get(category_id)
        if cat is None:
            raise CategoryNotFoundError(category_id)
        return cat

    def update_category(self, category_id: str, **updates: Any) -> WorkflowTemplateCategory:
        existing = self.get_category(category_id)
        updated = existing.model_copy(update=updates)
        self._categories[category_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                CategoryUpdated(
                    category_id=category_id,
                    category_name=updated.name,
                )
            )
        return updated

    def list_categories(self) -> list[WorkflowTemplateCategory]:
        return sorted(self._categories.values(), key=lambda c: c.order)

    def count_templates(self) -> int:
        return len(self._templates)

    def count_categories(self) -> int:
        return len(self._categories)


__all__ = ["WorkflowTemplateRegistry"]
