"""Tests for :mod:`eaip.hostdisc.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.hostdisc.models import DiscoveryConfig, DiscoveryJob, Host, HostStatus, JobStatus


class TestHost:
    def test_create_minimal(self) -> None:
        h = Host(id="h1", hostname="server01", ip_address="10.0.0.1")
        assert h.status is HostStatus.UNKNOWN
        assert h.tags == ()

    def test_frozen(self) -> None:
        h = Host(id="h1", hostname="srv", ip_address="10.0.0.1")
        with pytest.raises(ValidationError):
            h.hostname = "changed"


class TestDiscoveryJob:
    def test_create_minimal(self) -> None:
        j = DiscoveryJob(id="j1", cidr_range="10.0.0.0/24")
        assert j.status is JobStatus.RUNNING
        assert j.ports == ()

    def test_frozen(self) -> None:
        j = DiscoveryJob(id="j1", cidr_range="10.0.0.0/24")
        with pytest.raises(ValidationError):
            j.status = JobStatus.COMPLETED


class TestDiscoveryConfig:
    def test_defaults(self) -> None:
        c = DiscoveryConfig()
        assert c.default_cidr == "10.0.0.0/24"
        assert c.default_ports == (22, 80, 443)

    def test_frozen(self) -> None:
        c = DiscoveryConfig()
        with pytest.raises(ValidationError):
            c.scan_timeout_seconds = 60


class TestHostStatus:
    def test_values(self) -> None:
        assert HostStatus.ONLINE.value == "online"
        assert HostStatus.OFFLINE.value == "offline"
        assert HostStatus.UNKNOWN.value == "unknown"


class TestJobStatus:
    def test_values(self) -> None:
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Host(id="h1", hostname="srv", ip_address="10.0.0.1", unknown="x")
