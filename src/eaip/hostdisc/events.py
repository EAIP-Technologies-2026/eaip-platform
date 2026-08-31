"""Domain events for host discovery."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.hostdisc.models import HostStatus


class HostDiscovered(DomainEvent):
    event_type: ClassVar[str] = "eaip.hostdisc.host.discovered"

    host_id: str
    hostname: str
    ip_address: str
    os: str = Field(default="")


class HostStatusChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.hostdisc.host.status_changed"

    host_id: str
    previous_status: HostStatus
    new_status: HostStatus


class DiscoveryCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.hostdisc.discovery.completed"

    job_id: str
    cidr_range: str
    total_hosts: int
    completed_hosts: int


__all__ = [
    "DiscoveryCompleted",
    "HostDiscovered",
    "HostStatusChanged",
]
