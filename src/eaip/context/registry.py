"""PromptRegistry — in-memory registry for prompt templates with versioning and observer support."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from eaip.context.exceptions import PromptNotFoundError
from eaip.context.models import PromptRegistryEntry, PromptTemplate, PromptVersion
from eaip.logging.context import get_logger


@dataclass
class Observer:
    """An observer subscribed to prompt registry events.

    Attributes:
        name: Human-readable name for logging.
        callback: Callable invoked with the event payload.
    """

    name: str
    callback: Callable[[str, dict[str, Any]], None]


class PromptRegistry:
    """In-memory registry for prompt templates with versioning and observer support.

    Manages prompt lifecycle including registration, version management,
    and change notification via the Observer pattern.
    """

    def __init__(self) -> None:
        """Initialize an empty PromptRegistry."""
        self._entries: dict[str, PromptRegistryEntry] = {}
        self._templates: dict[str, PromptTemplate] = {}
        self._observers: list[Observer] = []
        self._log = get_logger("eaip.context.registry")

    # ------------------------------------------------------------------
    # Observer management
    # ------------------------------------------------------------------

    def attach(self, name: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        """Register an observer.

        Args:
            name: Observer name for logging.
            callback: Callable receiving (event_type, payload).
        """
        self._observers.append(Observer(name=name, callback=callback))
        self._log.debug("observer.attached", name=name)

    def detach(self, name: str) -> None:
        """Remove an observer by name.

        Args:
            name: The observer name to remove.
        """
        self._observers[:] = [o for o in self._observers if o.name != name]
        self._log.debug("observer.detached", name=name)

    def _notify(self, event_type: str, **payload: Any) -> None:
        """Notify all observers of an event.

        Args:
            event_type: The event type string.
            payload: Additional event data.
        """
        for observer in self._observers:
            try:
                observer.callback(event_type, payload)
            except Exception as exc:
                self._log.warning(
                    "observer.failed",
                    name=observer.name,
                    error=str(exc),
                )

    # ------------------------------------------------------------------
    # Prompt & version management
    # ------------------------------------------------------------------

    def register(self, prompt: PromptTemplate) -> PromptRegistryEntry:
        """Register a new prompt template with its initial version.

        Args:
            prompt: The prompt template to register.

        Returns:
            The created PromptRegistryEntry.
        """
        version = PromptVersion(
            version=prompt.version,
            content=prompt.content,
            author="",
            metadata={"template_id": prompt.template_id},
        )
        entry = PromptRegistryEntry(
            prompt_id=prompt.template_id,
            current_version=prompt.version,
            versions=(version,),
            metadata=prompt.metadata,
        )
        self._entries[prompt.template_id] = entry
        self._templates[prompt.template_id] = prompt
        self._log.info("registry.register", template_id=prompt.template_id, version=prompt.version)
        self._notify("registered", prompt_id=prompt.template_id, version=prompt.version)
        return entry

    def get(self, prompt_id: str) -> PromptTemplate:
        """Get a prompt template by its ID.

        Args:
            prompt_id: The unique prompt identifier.

        Returns:
            The matching PromptTemplate.

        Raises:
            PromptNotFoundError: If the prompt is not registered.
        """
        template = self._templates.get(prompt_id)
        if template is None:
            raise PromptNotFoundError(f"Prompt {prompt_id!r} not found")
        return template

    def get_entry(self, prompt_id: str) -> PromptRegistryEntry:
        """Get the full registry entry for a prompt.

        Args:
            prompt_id: The unique prompt identifier.

        Returns:
            The matching PromptRegistryEntry.

        Raises:
            PromptNotFoundError: If the prompt is not registered.
        """
        entry = self._entries.get(prompt_id)
        if entry is None:
            raise PromptNotFoundError(f"Prompt entry {prompt_id!r} not found")
        return entry

    def get_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Get a specific version of a prompt.

        Args:
            prompt_id: The unique prompt identifier.
            version: The version string to retrieve.

        Returns:
            The matching PromptVersion.

        Raises:
            PromptNotFoundError: If the prompt or version is not found.
        """
        entry = self.get_entry(prompt_id)
        for v in entry.versions:
            if v.version == version:
                return v
        raise PromptNotFoundError(f"Version {version!r} for prompt {prompt_id!r} not found")

    def add_version(
        self,
        prompt_id: str,
        version: PromptVersion,
        *,
        set_current: bool = True,
    ) -> PromptRegistryEntry:
        """Add a new version to an existing prompt.

        Args:
            prompt_id: The unique prompt identifier.
            version: The new version to add.
            set_current: Whether to set this version as the current one.

        Returns:
            The updated PromptRegistryEntry.

        Raises:
            PromptNotFoundError: If the prompt is not registered.
        """
        entry = self.get_entry(prompt_id)
        existing_versions = [v for v in entry.versions if v.version == version.version]
        if existing_versions:
            self._log.warning("version.exists", prompt_id=prompt_id, version=version.version)

        new_versions = (*entry.versions, version)
        new_entry = PromptRegistryEntry(
            prompt_id=entry.prompt_id,
            current_version=version.version if set_current else entry.current_version,
            versions=new_versions,
            metadata=entry.metadata,
        )
        self._entries[prompt_id] = new_entry

        if set_current:
            template = self._templates.get(prompt_id)
            if template is not None:
                self._templates[prompt_id] = PromptTemplate(
                    template_id=template.template_id,
                    name=template.name,
                    description=template.description,
                    content=version.content,
                    variables=template.variables,
                    version=version.version,
                    metadata=template.metadata,
                )

        self._log.info("registry.add_version", prompt_id=prompt_id, version=version.version)
        self._notify("versioned", prompt_id=prompt_id, version=version.version)
        return new_entry

    def list_prompts(self) -> list[PromptTemplate]:
        """List all registered prompt templates.

        Returns:
            A list of all registered PromptTemplate objects.
        """
        return list(self._templates.values())

    def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        """List all versions of a registered prompt.

        Args:
            prompt_id: The unique prompt identifier.

        Returns:
            A list of PromptVersion objects.

        Raises:
            PromptNotFoundError: If the prompt is not registered.
        """
        entry = self.get_entry(prompt_id)
        return list(entry.versions)

    def remove(self, prompt_id: str) -> bool:
        """Remove a prompt and all its versions from the registry.

        Args:
            prompt_id: The unique prompt identifier.

        Returns:
            True if the prompt was removed, False if not found.
        """
        found = self._entries.pop(prompt_id, None)
        self._templates.pop(prompt_id, None)
        if found is not None:
            self._log.info("registry.remove", prompt_id=prompt_id)
            self._notify("removed", prompt_id=prompt_id)
            return True
        return False

    def clear(self) -> None:
        """Remove all prompts from the registry."""
        self._entries.clear()
        self._templates.clear()
        self._log.debug("registry.cleared")

    @property
    def count(self) -> int:
        """Return the number of registered prompts."""
        return len(self._entries)

    async def health(self) -> dict[str, object]:
        """Return health status for this registry.

        Returns:
            A dict with health information.
        """
        return {
            "status": "healthy",
            "prompts": self.count,
        }


__all__ = ["Observer", "PromptRegistry"]
