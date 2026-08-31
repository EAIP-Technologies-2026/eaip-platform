"""Tests for endpointsec domain events."""

from __future__ import annotations

import pytest

from eaip.endpointsec.events import (
    EndpointRegistered,
    FindingReported,
    FindingResolved,
    ScanCompleted,
)
from eaip.endpointsec.models import Severity
from eaip.events.event import DomainEvent


class TestEndpointRegistered:
    def test_defaults(self) -> None:
        e = EndpointRegistered(endpoint_id="ep1", name="api-gw", host="10.0.0.1", port=443)
        assert e.event_type == "eaip.endpointsec.endpoint.registered"
        assert isinstance(e, DomainEvent)


class TestScanCompleted:
    def test_defaults(self) -> None:
        e = ScanCompleted(endpoint_id="ep1", scan_id="sc1")
        assert e.event_type == "eaip.endpointsec.scan.completed"
        assert e.total_findings == 0

    def test_with_values(self) -> None:
        e = ScanCompleted(
            endpoint_id="ep1",
            scan_id="sc1",
            total_findings=3,
            critical_count=1,
            duration_seconds=45.2,
        )
        assert e.total_findings == 3
        assert e.critical_count == 1
        assert e.duration_seconds == 45.2


class TestFindingReported:
    def test_defaults(self) -> None:
        e = FindingReported(finding_id="f1", endpoint_id="ep1", severity=Severity.HIGH)
        assert e.event_type == "eaip.endpointsec.finding.reported"
        assert e.cve_id == ""

    def test_with_values(self) -> None:
        e = FindingReported(
            finding_id="f1", endpoint_id="ep1", severity=Severity.CRITICAL, cve_id="CVE-2025-0001"
        )
        assert e.cve_id == "CVE-2025-0001"
        assert e.severity == Severity.CRITICAL

    def test_frozen(self) -> None:
        e = FindingReported(finding_id="f1", endpoint_id="ep1", severity=Severity.MEDIUM)
        with pytest.raises((ValueError, TypeError)):
            e.finding_id = "f2"


class TestFindingResolved:
    def test_defaults(self) -> None:
        e = FindingResolved(finding_id="f1", endpoint_id="ep1", severity=Severity.LOW)
        assert e.event_type == "eaip.endpointsec.finding.resolved"

    def test_with_values(self) -> None:
        e = FindingResolved(finding_id="f1", endpoint_id="ep1", severity=Severity.HIGH)
        assert e.severity == Severity.HIGH


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [EndpointRegistered, ScanCompleted, FindingReported, FindingResolved]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
