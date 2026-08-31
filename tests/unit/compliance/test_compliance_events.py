from __future__ import annotations

import pydantic
import pytest

from eaip.compliance.events import (
    ComplianceScanCompleted,
    ComplianceScanStarted,
    ControlStatusChanged,
    EvidenceCollected,
    RemediationCreated,
    RemediationResolved,
)


class TestComplianceEvents:
    def test_compliance_scan_started(self) -> None:
        event = ComplianceScanStarted(regulation_id="gdpr", scan_id="s1")
        assert event.event_type == "compliance.scan.started"
        assert event.regulation_id == "gdpr"
        assert event.scan_id == "s1"

    def test_compliance_scan_completed(self) -> None:
        event = ComplianceScanCompleted(
            regulation_id="gdpr", scan_id="s1", score=85.5, status="partially_compliant"
        )
        assert event.event_type == "compliance.scan.completed"
        assert event.regulation_id == "gdpr"
        assert event.scan_id == "s1"
        assert event.score == 85.5
        assert event.status == "partially_compliant"

    def test_control_status_changed(self) -> None:
        event = ControlStatusChanged(
            control_id="c1", previous_status="unknown", new_status="compliant"
        )
        assert event.event_type == "compliance.control.status_changed"
        assert event.control_id == "c1"
        assert event.previous_status == "unknown"
        assert event.new_status == "compliant"

    def test_remediation_created(self) -> None:
        event = RemediationCreated(item_id="r1", control_id="c1", description="fix it")
        assert event.event_type == "compliance.remediation.created"
        assert event.item_id == "r1"
        assert event.control_id == "c1"
        assert event.description == "fix it"

    def test_remediation_resolved(self) -> None:
        event = RemediationResolved(item_id="r1", control_id="c1")
        assert event.event_type == "compliance.remediation.resolved"
        assert event.item_id == "r1"
        assert event.control_id == "c1"

    def test_evidence_collected(self) -> None:
        event = EvidenceCollected(evidence_id="e1", control_id="c1", source="audit")
        assert event.event_type == "compliance.evidence.collected"
        assert event.evidence_id == "e1"
        assert event.control_id == "c1"
        assert event.source == "audit"

    def test_frozen(self) -> None:
        event = ComplianceScanStarted(regulation_id="gdpr", scan_id="s1")
        with pytest.raises(pydantic.ValidationError):
            event.regulation_id = "hipaa"  # type: ignore[misc]

    def test_occurred_at_default(self) -> None:
        event = ComplianceScanStarted(regulation_id="gdpr", scan_id="s1")
        assert event.occurred_at is not None
