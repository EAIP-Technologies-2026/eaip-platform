"""Tests for depscan domain events."""

from __future__ import annotations

import pytest

from eaip.depscan.events import ScanCompleted, ScanStarted, VulnerabilityFound
from eaip.depscan.models import Severity
from eaip.events.event import DomainEvent


class TestScanStarted:
    def test_defaults(self) -> None:
        e = ScanStarted(scan_id="sc1", target_id="t1", started_at="2025-01-01T00:00:00Z")  # type: ignore[arg-type]
        assert e.event_type == "eaip.depscan.scan.started"
        assert isinstance(e, DomainEvent)


class TestScanCompleted:
    def test_defaults(self) -> None:
        e = ScanCompleted(scan_id="sc1", target_id="t1")
        assert e.event_type == "eaip.depscan.scan.completed"
        assert e.total_vulnerabilities == 0

    def test_with_values(self) -> None:
        e = ScanCompleted(
            scan_id="sc1",
            target_id="t1",
            total_vulnerabilities=5,
            success=True,
            duration_seconds=12.3,
        )
        assert e.total_vulnerabilities == 5
        assert e.duration_seconds == 12.3


class TestVulnerabilityFound:
    def test_defaults(self) -> None:
        e = VulnerabilityFound(vulnerability_id="v1", target_id="t1", severity=Severity.HIGH)
        assert e.event_type == "eaip.depscan.vulnerability.found"
        assert e.cve_id == ""

    def test_with_values(self) -> None:
        e = VulnerabilityFound(
            vulnerability_id="v1",
            target_id="t1",
            cve_id="CVE-2025-0001",
            severity=Severity.CRITICAL,
        )
        assert e.cve_id == "CVE-2025-0001"
        assert e.severity == Severity.CRITICAL

    def test_frozen(self) -> None:
        e = VulnerabilityFound(vulnerability_id="v1", target_id="t1", severity=Severity.MEDIUM)
        with pytest.raises((ValueError, TypeError)):
            e.vulnerability_id = "v2"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [ScanStarted, ScanCompleted, VulnerabilityFound]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
