"""Tests for :mod:`eaip.hostdisc.events`."""

from __future__ import annotations

import pytest

from eaip.hostdisc.events import (
    DiscoveryCompleted,
    HostDiscovered,
    HostStatusChanged,
)
from eaip.hostdisc.models import HostStatus


class TestHostDiscovered:
    def test_create(self) -> None:
        e = HostDiscovered(host_id="h1", hostname="server01", ip_address="10.0.0.1")
        assert e.event_type == "eaip.hostdisc.host.discovered"

    def test_frozen(self) -> None:
        e = HostDiscovered(host_id="h1", hostname="n", ip_address="ip")
        with pytest.raises(ValueError):
            e.host_id = "h2"


class TestHostStatusChanged:
    def test_create(self) -> None:
        e = HostStatusChanged(
            host_id="h1", previous_status=HostStatus.UNKNOWN, new_status=HostStatus.ONLINE
        )
        assert e.event_type == "eaip.hostdisc.host.status_changed"


class TestDiscoveryCompleted:
    def test_create(self) -> None:
        e = DiscoveryCompleted(
            job_id="j1", cidr_range="10.0.0.0/24", total_hosts=10, completed_hosts=10
        )
        assert e.event_type == "eaip.hostdisc.discovery.completed"


def test_all_events_have_unique_types() -> None:
    types = [
        HostDiscovered(host_id="h", hostname="n", ip_address="ip").event_type,
        HostStatusChanged(
            host_id="h", previous_status=HostStatus.UNKNOWN, new_status=HostStatus.ONLINE
        ).event_type,
        DiscoveryCompleted(job_id="j", cidr_range="c", total_hosts=1, completed_hosts=1).event_type,
    ]
    assert len(types) == len(set(types))
