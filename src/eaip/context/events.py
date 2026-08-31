"""Context & Prompt Intelligence domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContextEvent(DomainEvent):
    """Base event for all Context & Prompt Intelligence events."""

    event_type: ClassVar[str] = "eaip.context.event"


class PromptCreated(ContextEvent):
    """Published when a new prompt template is created."""

    event_type: ClassVar[str] = "eaip.context.prompt.created"
    prompt_id: str
    name: str
    version: str


class PromptVersioned(ContextEvent):
    """Published when a new version of a prompt is registered."""

    event_type: ClassVar[str] = "eaip.context.prompt.versioned"
    prompt_id: str
    version: str
    author: str = ""


class ContextAssembled(ContextEvent):
    """Published after context is assembled from sources."""

    event_type: ClassVar[str] = "eaip.context.assembled"
    document_count: int
    total_tokens: int
    duration_ms: float


class ContextCompressed(ContextEvent):
    """Published after context is compressed."""

    event_type: ClassVar[str] = "eaip.context.compressed"
    original_tokens: int
    compressed_tokens: int
    strategy: str
    ratio: float


class PromptVersionCompared(DomainEvent):
    event_type: ClassVar[str] = "eaip.context.prompt.version.compared"
    prompt_id: str
    version_a: str
    version_b: str


class PromptRolledBack(DomainEvent):
    event_type: ClassVar[str] = "eaip.context.prompt.rolled.back"
    prompt_id: str
    target_version: str


__all__ = [
    "ContextAssembled",
    "ContextCompressed",
    "ContextEvent",
    "PromptCreated",
    "PromptRolledBack",
    "PromptVersionCompared",
    "PromptVersioned",
]
