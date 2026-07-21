"""Prompt service — prompt catalog, A/B testing, version comparison, rollback."""

from __future__ import annotations

from typing import Any

from eaip.context.events import PromptRolledBack, PromptVersionCompared
from eaip.context.models import PromptTemplate, PromptVersion
from eaip.context.registry import PromptRegistry
from eaip.logging.context import get_logger


class PromptService:
    def __init__(self, registry: PromptRegistry, event_bus: Any = None) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._log = get_logger("eaip.context.prompt_service")

    @property
    def registry(self) -> PromptRegistry:
        return self._registry

    def create_prompt(
        self, prompt_id: str, name: str, content: str, description: str = ""
    ) -> PromptTemplate:
        template = PromptTemplate(
            template_id=prompt_id, name=name, content=content, description=description
        )
        self._registry.register(template)
        return template

    def get_prompt(self, prompt_id: str) -> PromptTemplate:
        return self._registry.get(prompt_id)

    def list_prompts(self) -> list[PromptTemplate]:
        return self._registry.list_prompts()

    def get_version(self, prompt_id: str, version: str) -> PromptVersion:
        return self._registry.get_version(prompt_id, version)

    def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        return self._registry.list_versions(prompt_id)

    def add_version(
        self, prompt_id: str, content: str, change_log: str = "", author: str = ""
    ) -> PromptTemplate:
        current = self._registry.get(prompt_id)
        parts = current.version.split(".")
        new_version_str = f"{parts[0]}.{int(parts[1]) + 1}.0"
        version = PromptVersion(
            version=new_version_str, content=content, change_log=change_log, author=author
        )
        self._registry.add_version(prompt_id, version)
        return self._registry.get(prompt_id)

    def compare_versions(self, prompt_id: str, version_a: str, version_b: str) -> dict[str, Any]:
        va = self._registry.get_version(prompt_id, version_a)
        vb = self._registry.get_version(prompt_id, version_b)
        result: dict[str, Any] = {
            "prompt_id": prompt_id,
            "version_a": version_a,
            "version_b": version_b,
            "content_changed": va.content != vb.content,
        }
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        PromptVersionCompared(
                            prompt_id=prompt_id,
                            version_a=version_a,
                            version_b=version_b,
                        )
                    )
                )
            except Exception:
                pass
        return result

    def rollback(self, prompt_id: str, target_version: str) -> PromptTemplate:
        target = self._registry.get_version(prompt_id, target_version)
        current = self._registry.get(prompt_id)
        versions = self._registry.list_versions(prompt_id)
        new_version_str = f"{current.version}.rollback"
        rollback_version = PromptVersion(
            version=new_version_str,
            content=target.content,
            change_log=f"Rollback to {target_version}",
        )
        self._registry.add_version(prompt_id, rollback_version)
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        PromptRolledBack(
                            prompt_id=prompt_id,
                            target_version=target_version,
                        )
                    )
                )
            except Exception:
                pass
        return self._registry.get(prompt_id)

    def search_prompts(self, query: str) -> list[PromptTemplate]:
        q = query.lower()
        return [
            p
            for p in self._registry.list_prompts()
            if q in p.name.lower() or q in p.content.lower()
        ]


__all__ = ["PromptService"]
