"""Domain events for Helm chart repository."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ChartUploaded(DomainEvent):
    event_type: ClassVar[str] = "eaip.helmrepo.chart.uploaded"

    chart_id: str
    name: str
    version: str


class ChartDeprecated(DomainEvent):
    event_type: ClassVar[str] = "eaip.helmrepo.chart.deprecated"

    chart_id: str
    name: str
    reason: str = Field(default="")


class ReleaseDeployed(DomainEvent):
    event_type: ClassVar[str] = "eaip.helmrepo.release.deployed"

    release_id: str
    chart_id: str
    environment: str
    revision: int


class ReleaseRolledBack(DomainEvent):
    event_type: ClassVar[str] = "eaip.helmrepo.release.rolled_back"

    release_id: str
    chart_id: str
    environment: str
    previous_revision: int
    new_revision: int


__all__ = [
    "ChartDeprecated",
    "ChartUploaded",
    "ReleaseDeployed",
    "ReleaseRolledBack",
]
