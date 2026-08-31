"""Domain events for Git integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class RepositoryRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.gitsvc.repository.registered"

    repo_id: str
    name: str
    url: str
    provider: str


class CommitIndexed(DomainEvent):
    event_type: ClassVar[str] = "eaip.gitsvc.commit.indexed"

    repo_id: str
    sha: str
    author: str
    files_changed: int


class WebhookReceived(DomainEvent):
    event_type: ClassVar[str] = "eaip.gitsvc.webhook.received"

    repo_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class BranchUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.gitsvc.branch.updated"

    repo_id: str
    branch: str
    old_sha: str
    new_sha: str
    timestamp: datetime


__all__ = [
    "BranchUpdated",
    "CommitIndexed",
    "RepositoryRegistered",
    "WebhookReceived",
]
