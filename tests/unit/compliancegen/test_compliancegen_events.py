"""Tests for compliance report generator domain events."""

from __future__ import annotations

import pydantic
import pytest

from eaip.compliancegen.events import FindingReported, ScanCompleted, ScanStarted


class TestScanStarted:
    def test_create(self) -> None:
        event = ScanStarted(scan_id="s1", framework_id="nist", target="acme-vm")
        assert event.scan_id == "s1"
        assert event.framework_id == "nist"
        assert event.target == "acme-vm"
        assert event.event_type == "eaip.compliancegen.scan_started"


class TestScanCompleted:
    def test_create(self) -> None:
        event = ScanCompleted(scan_id="s1", finding_count=10, passed=8, failed=1, warnings=1)
        assert event.finding_count == 10
        assert event.passed == 8
        assert event.failed == 1
        assert event.event_type == "eaip.compliancegen.scan_completed"


class TestFindingReported:
    def test_create(self) -> None:
        event = FindingReported(finding_id="f1", scan_id="s1", control_id="ac-1", status="fail")
        assert event.finding_id == "f1"
        assert event.status == "fail"
        assert event.event_type == "eaip.compliancegen.finding_reported"

    def test_frozen(self) -> None:
        event = FindingReported(finding_id="f1", scan_id="s1", control_id="ac-1", status="fail")
        with pytest.raises(pydantic.ValidationError):
            event.finding_id = "f2"  # type: ignore[misc]
