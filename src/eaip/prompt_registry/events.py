"""Prompt Registry domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class PromptRegistryEvent(DomainEvent):
    """Base event for all Prompt Registry events."""

    event_type: ClassVar[str] = "eaip.prompt_registry.event"


class PromptCreated(PromptRegistryEvent):
    """Published when a new prompt definition is created."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.created"
    prompt_id: str
    name: str
    category: str = ""


class PromptUpdated(PromptRegistryEvent):
    """Published when a prompt definition is updated."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.updated"
    prompt_id: str
    changes: tuple[str, ...] = ()


class PromptDeleted(PromptRegistryEvent):
    """Published when a prompt definition is deleted."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.deleted"
    prompt_id: str


class PromptVersionCreated(PromptRegistryEvent):
    """Published when a new version is added to a prompt."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.created"
    prompt_id: str
    version: str
    author: str = ""


class PromptVersionActivated(PromptRegistryEvent):
    """Published when a version is activated as the current version."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.activated"
    prompt_id: str
    version: str


class PromptVersionDeactivated(PromptRegistryEvent):
    """Published when a version is deactivated."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.deactivated"
    prompt_id: str
    version: str


class PromptVersionArchived(PromptRegistryEvent):
    """Published when a version is archived."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.archived"
    prompt_id: str
    version: str


class PromptVersionRolledBack(PromptRegistryEvent):
    """Published when the prompt is rolled back to a previous version."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.rolled_back"
    prompt_id: str
    target_version: str
    previous_version: str


class PromptVersionCompared(PromptRegistryEvent):
    """Published when two versions of a prompt are compared."""

    event_type: ClassVar[str] = "eaip.prompt_registry.version.compared"
    prompt_id: str
    version_a: str
    version_b: str


class PromptPublished(PromptRegistryEvent):
    """Published when a prompt is published (promoted to active)."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.published"
    prompt_id: str
    version: str


class PromptArchived(PromptRegistryEvent):
    """Published when a prompt is archived."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.archived"
    prompt_id: str


class PromptApproved(PromptRegistryEvent):
    """Published when a prompt version is approved by a reviewer."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.approved"
    prompt_id: str
    version: str
    reviewer: str = ""


class PromptRejected(PromptRegistryEvent):
    """Published when a prompt version is rejected by a reviewer."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.rejected"
    prompt_id: str
    version: str
    reviewer: str = ""
    reason: str = ""


class PromptSearched(PromptRegistryEvent):
    """Published when a search is performed on the registry."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.searched"
    query: str = ""
    total_results: int = 0


class PromptRegistered(PromptRegistryEvent):
    """Published when a prompt is registered in the registry."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.registered"
    prompt_id: str
    name: str


class PromptUnregistered(PromptRegistryEvent):
    """Published when a prompt is unregistered from the registry."""

    event_type: ClassVar[str] = "eaip.prompt_registry.prompt.unregistered"
    prompt_id: str


__all__ = [
    "PromptApproved",
    "PromptArchived",
    "PromptCreated",
    "PromptDeleted",
    "PromptPublished",
    "PromptRegistered",
    "PromptRegistryEvent",
    "PromptRejected",
    "PromptSearched",
    "PromptUnregistered",
    "PromptUpdated",
    "PromptVersionActivated",
    "PromptVersionArchived",
    "PromptVersionCompared",
    "PromptVersionCreated",
    "PromptVersionDeactivated",
    "PromptVersionRolledBack",
]
