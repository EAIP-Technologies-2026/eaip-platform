"""Tests for audit domain events."""

from __future__ import annotations

from eaip.audit.events import (
    AuditEventLogged,
    AuditPolicyCreated,
    AuditPolicyUpdated,
    ComplianceReportGenerated,
    DataClassified,
    LegalHoldCreated,
    LegalHoldReleased,
    RetentionApplied,
)
from eaip.audit.models import (
    AuditEvent,
    AuditPolicy,
    ClassificationLevel,
    DataClassification,
    LegalHold,
)
from eaip.events.event import DomainEvent


class TestAuditEventLogged:
    def test_event_type(self) -> None:
        audit_event = AuditEvent(
            id="e1",
            event_type="test",
            actor_id="a",
            actor_type="user",
            action="act",
            resource_type="rt",
            resource_id="ri",
        )
        event = AuditEventLogged(audit_event=audit_event)
        assert event.event_type == "audit.event.logged"
        assert isinstance(event, DomainEvent)

    def test_content(self) -> None:
        audit_event = AuditEvent(
            id="e1",
            event_type="user.login",
            actor_id="u1",
            actor_type="user",
            action="login",
            resource_type="session",
            resource_id="s1",
        )
        event = AuditEventLogged(audit_event=audit_event)
        assert event.audit_event.id == "e1"
        assert event.audit_event.event_type == "user.login"


class TestAuditPolicyCreated:
    def test_event_type(self) -> None:
        policy = AuditPolicy(id="p1", name="Test Policy")
        event = AuditPolicyCreated(policy=policy)
        assert event.event_type == "audit.policy.created"

    def test_content(self) -> None:
        policy = AuditPolicy(id="p1", name="Retention Policy", retention_days=365)
        event = AuditPolicyCreated(policy=policy)
        assert event.policy.name == "Retention Policy"
        assert event.policy.retention_days == 365


class TestAuditPolicyUpdated:
    def test_event_type(self) -> None:
        event = AuditPolicyUpdated(policy_id="p1", changes={"name": "Updated"})
        assert event.event_type == "audit.policy.updated"

    def test_fields(self) -> None:
        event = AuditPolicyUpdated(policy_id="p1", changes={"retention_days": 365})
        assert event.policy_id == "p1"
        assert event.changes == {"retention_days": 365}


class TestDataClassified:
    def test_event_type(self) -> None:
        dc = DataClassification(id="dc1", name="PII", level=ClassificationLevel.RESTRICTED)
        event = DataClassified(data_type="pii", classification=dc)
        assert event.event_type == "audit.data.classified"

    def test_content(self) -> None:
        dc = DataClassification(id="dc1", name="PII", level=ClassificationLevel.CONFIDENTIAL)
        event = DataClassified(data_type="pii", classification=dc)
        assert event.data_type == "pii"
        assert event.classification.level == ClassificationLevel.CONFIDENTIAL


class TestRetentionApplied:
    def test_event_type(self) -> None:
        event = RetentionApplied(rule_id="r1", data_type="logs", records_affected=100)
        assert event.event_type == "audit.retention.applied"

    def test_fields(self) -> None:
        event = RetentionApplied(rule_id="r1", data_type="audit_logs", records_affected=42)
        assert event.rule_id == "r1"
        assert event.data_type == "audit_logs"
        assert event.records_affected == 42


class TestLegalHoldCreated:
    def test_event_type(self) -> None:
        hold = LegalHold(id="lh1", name="Investigation", reason="Legal case")
        event = LegalHoldCreated(legal_hold=hold)
        assert event.event_type == "audit.legal_hold.created"

    def test_content(self) -> None:
        hold = LegalHold(id="lh1", name="GDPR Hold", reason="GDPR request")
        event = LegalHoldCreated(legal_hold=hold)
        assert event.legal_hold.name == "GDPR Hold"
        assert event.legal_hold.reason == "GDPR request"


class TestLegalHoldReleased:
    def test_event_type(self) -> None:
        event = LegalHoldReleased(legal_hold_id="lh1", reason="Case closed")
        assert event.event_type == "audit.legal_hold.released"

    def test_fields(self) -> None:
        event = LegalHoldReleased(legal_hold_id="lh1", reason="Completed")
        assert event.legal_hold_id == "lh1"
        assert event.reason == "Completed"


class TestComplianceReportGenerated:
    def test_event_type(self) -> None:
        event = ComplianceReportGenerated(
            framework="SOC2", status="pass", score=95.0, findings_count=5
        )
        assert event.event_type == "audit.compliance.report.generated"

    def test_fields(self) -> None:
        event = ComplianceReportGenerated(
            framework="HIPAA", status="fail", score=60.0, findings_count=3
        )
        assert event.framework == "HIPAA"
        assert event.status == "fail"
        assert event.score == 60.0
        assert event.findings_count == 3


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(AuditEventLogged, DomainEvent)
        assert issubclass(AuditPolicyCreated, DomainEvent)
        assert issubclass(AuditPolicyUpdated, DomainEvent)
        assert issubclass(DataClassified, DomainEvent)
        assert issubclass(RetentionApplied, DomainEvent)
        assert issubclass(LegalHoldCreated, DomainEvent)
        assert issubclass(LegalHoldReleased, DomainEvent)
        assert issubclass(ComplianceReportGenerated, DomainEvent)
