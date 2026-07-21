"""Tests for the audit enhancements subsystem."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.audit_enhancements.events import (
    AuditAggregationCompleted,
    AuditAlertResolved,
    AuditAlertTriggered,
    AuditCorrelationDetected,
    AuditCorrelationRuleCreated,
    AuditCorrelationRuleDeleted,
    AuditCorrelationRuleUpdated,
    AuditEnhancementConfigUpdated,
    AuditEnrichmentApplied,
    AuditEnrichmentRuleCreated,
    AuditReportGenerated,
    AuditStreamConfigured,
    AuditStreamStarted,
    AuditStreamStopped,
)
from eaip.audit_enhancements.exceptions import (
    AuditAggregationError,
    AuditAlertError,
    AuditCorrelationError,
    AuditEnhancementConfigError,
    AuditEnhancementError,
    AuditEnrichmentError,
    AuditReportError,
    AuditStreamError,
)
from eaip.audit_enhancements.health import AuditEnhancementHealthCheck
from eaip.audit_enhancements.models import (
    AuditAggregationResult,
    AuditAggregationRule,
    AuditAlertRule,
    AuditAlertSeverity,
    AuditCorrelationResult,
    AuditCorrelationRule,
    AuditEnhancementConfig,
    AuditEnhancementReport,
    AuditEnrichmentResult,
    AuditEnrichmentRule,
    AuditNotificationTarget,
    AuditRetentionRule,
    AuditStreamConfig,
    EnhancementType,
)
from eaip.audit_enhancements.service import AuditEnhancementService


class TestModels:
    def test_enhancement_type_values(self) -> None:
        assert EnhancementType.CORRELATION.value == "correlation"
        assert EnhancementType.ENRICHMENT.value == "enrichment"
        assert EnhancementType.AGGREGATION.value == "aggregation"
        assert EnhancementType.ALERT.value == "alert"
        assert EnhancementType.STREAM.value == "stream"

    def test_audit_alert_severity_values(self) -> None:
        assert AuditAlertSeverity.INFO.value == "info"
        assert AuditAlertSeverity.LOW.value == "low"
        assert AuditAlertSeverity.MEDIUM.value == "medium"
        assert AuditAlertSeverity.HIGH.value == "high"
        assert AuditAlertSeverity.CRITICAL.value == "critical"

    def test_correlation_rule_frozen(self) -> None:
        rule = AuditCorrelationRule(id="c1", name="test-correlation")
        with pytest.raises(AttributeError):
            rule.name = "changed"

    def test_audit_enhancement_config_defaults(self) -> None:
        config = AuditEnhancementConfig()
        assert config.enabled is True
        assert config.correlation_enabled is True
        assert config.enrichment_enabled is True
        assert config.aggregation_enabled is True
        assert config.alerts_enabled is True
        assert config.streaming_enabled is True
        assert config.max_correlation_window_seconds == 600
        assert config.default_batch_size == 100

    def test_audit_correlation_result_defaults(self) -> None:
        result = AuditCorrelationResult(rule_id="r1")
        assert result.source_event_ids == ()
        assert result.target_event_ids == ()
        assert result.correlation_id == ""

    def test_audit_enrichment_result_defaults(self) -> None:
        result = AuditEnrichmentResult(rule_id="r1", event_id="e1")
        assert result.provider == ""
        assert result.enrichment_data == {}

    def test_audit_aggregation_result_defaults(self) -> None:
        result = AuditAggregationResult(rule_id="r1")
        assert result.group_key == ""
        assert result.count == 0

    def test_audit_enhancement_report_defaults(self) -> None:
        report = AuditEnhancementReport(id="rpt1", type=EnhancementType.CORRELATION)
        assert report.rules_evaluated == 0
        assert report.rules_matched == 0

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            AuditCorrelationRule(id="c1", name="test", unknown_field="x")  # type: ignore[call-arg]


class TestEvents:
    def test_correlation_rule_created_event_type(self) -> None:
        rule = AuditCorrelationRule(id="c1", name="test")
        event = AuditCorrelationRuleCreated(rule=rule)
        assert event.event_type == "eaip.audit_enhancements.correlation_rule.created"

    def test_correlation_rule_updated_event(self) -> None:
        event = AuditCorrelationRuleUpdated(rule_id="c1", changes={"name": "new-name"})
        assert event.event_type == "eaip.audit_enhancements.correlation_rule.updated"

    def test_correlation_rule_deleted_event(self) -> None:
        event = AuditCorrelationRuleDeleted(rule_id="c1")
        assert event.event_type == "eaip.audit_enhancements.correlation_rule.deleted"

    def test_correlation_detected_event(self) -> None:
        result = AuditCorrelationResult(rule_id="r1")
        event = AuditCorrelationDetected(result=result)
        assert event.event_type == "eaip.audit_enhancements.correlation.detected"

    def test_enrichment_rule_created_event(self) -> None:
        rule = AuditEnrichmentRule(id="e1", name="test-enrich")
        event = AuditEnrichmentRuleCreated(rule=rule)
        assert event.event_type == "eaip.audit_enhancements.enrichment_rule.created"

    def test_enrichment_applied_event(self) -> None:
        result = AuditEnrichmentResult(rule_id="e1", event_id="ev1")
        event = AuditEnrichmentApplied(result=result)
        assert event.event_type == "eaip.audit_enhancements.enrichment.applied"

    def test_aggregation_completed_event(self) -> None:
        result = AuditAggregationResult(rule_id="a1")
        event = AuditAggregationCompleted(result=result)
        assert event.event_type == "eaip.audit_enhancements.aggregation.completed"

    def test_alert_triggered_event(self) -> None:
        rule = AuditAlertRule(id="al1", name="test-alert")
        event = AuditAlertTriggered(alert_rule=rule, event_id="ev1")
        assert event.event_type == "eaip.audit_enhancements.alert.triggered"

    def test_alert_resolved_event(self) -> None:
        event = AuditAlertResolved(rule_id="al1", resolved_at=datetime.now(UTC))
        assert event.event_type == "eaip.audit_enhancements.alert.resolved"

    def test_stream_configured_event(self) -> None:
        config = AuditStreamConfig(id="s1", name="test-stream")
        event = AuditStreamConfigured(config=config)
        assert event.event_type == "eaip.audit_enhancements.stream.configured"

    def test_stream_started_event(self) -> None:
        event = AuditStreamStarted(stream_id="s1")
        assert event.event_type == "eaip.audit_enhancements.stream.started"

    def test_stream_stopped_event(self) -> None:
        event = AuditStreamStopped(stream_id="s1")
        assert event.event_type == "eaip.audit_enhancements.stream.stopped"

    def test_report_generated_event(self) -> None:
        report = AuditEnhancementReport(id="r1", type=EnhancementType.CORRELATION)
        event = AuditReportGenerated(report=report)
        assert event.event_type == "eaip.audit_enhancements.report.generated"

    def test_config_updated_event(self) -> None:
        config = AuditEnhancementConfig()
        event = AuditEnhancementConfigUpdated(config=config)
        assert event.event_type == "eaip.audit_enhancements.config.updated"


class TestExceptions:
    def test_audit_enhancement_error(self) -> None:
        exc = AuditEnhancementError("something went wrong")
        assert "something went wrong" in str(exc)

    def test_audit_correlation_error(self) -> None:
        exc = AuditCorrelationError("correlation failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_enrichment_error(self) -> None:
        exc = AuditEnrichmentError("enrichment failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_aggregation_error(self) -> None:
        exc = AuditAggregationError("aggregation failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_alert_error(self) -> None:
        exc = AuditAlertError("alert failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_stream_error(self) -> None:
        exc = AuditStreamError("stream failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_report_error(self) -> None:
        exc = AuditReportError("report failed")
        assert isinstance(exc, AuditEnhancementError)

    def test_audit_enhancement_config_error(self) -> None:
        exc = AuditEnhancementConfigError("invalid config")
        assert isinstance(exc, AuditEnhancementError)


class TestAuditEnhancementService:
    def test_initial_config(self) -> None:
        service = AuditEnhancementService()
        assert service.config.enabled is True

    def test_update_config(self) -> None:
        service = AuditEnhancementService()
        updated = service.update_config(enabled=False)
        assert updated.enabled is False
        assert service.config.enabled is False

    def test_create_and_get_correlation_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditCorrelationRule(id="c1", name="test")
        service.create_correlation_rule(rule)
        assert service.get_correlation_rule("c1").name == "test"

    def test_get_correlation_rule_not_found(self) -> None:
        service = AuditEnhancementService()
        with pytest.raises(AuditCorrelationError):
            service.get_correlation_rule("nonexistent")

    def test_update_correlation_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditCorrelationRule(id="c1", name="original")
        service.create_correlation_rule(rule)
        service.update_correlation_rule("c1", name="updated")
        assert service.get_correlation_rule("c1").name == "updated"

    def test_delete_correlation_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditCorrelationRule(id="c1", name="test")
        service.create_correlation_rule(rule)
        service.delete_correlation_rule("c1")
        assert len(service.list_correlation_rules()) == 0

    def test_correlate_events(self) -> None:
        service = AuditEnhancementService()
        rule = AuditCorrelationRule(id="c1", name="test")
        service.create_correlation_rule(rule)
        result = service.correlate_events(["s1"], ["t1"], "c1")
        assert result.rule_id == "c1"
        assert result.source_event_ids == ("s1",)
        assert result.target_event_ids == ("t1",)

    def test_correlate_events_disabled(self) -> None:
        service = AuditEnhancementService()
        service.update_config(correlation_enabled=False)
        with pytest.raises(AuditCorrelationError):
            service.correlate_events(["s1"], ["t1"], "nonexistent")

    def test_create_and_get_enrichment_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditEnrichmentRule(id="e1", name="test-enrich")
        service.create_enrichment_rule(rule)
        assert service.get_enrichment_rule("e1").name == "test-enrich"

    def test_enrich_event(self) -> None:
        service = AuditEnhancementService()
        rule = AuditEnrichmentRule(id="e1", name="test", enrichment_providers=("geoip",))
        service.create_enrichment_rule(rule)
        result = service.enrich_event("ev1", "e1", {"country": "US"})
        assert result.event_id == "ev1"
        assert result.provider == "geoip"
        assert result.enrichment_data == {"country": "US"}

    def test_create_and_get_aggregation_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditAggregationRule(id="a1", name="test-agg")
        service.create_aggregation_rule(rule)
        assert service.get_aggregation_rule("a1").name == "test-agg"

    def test_aggregate_events(self) -> None:
        service = AuditEnhancementService()
        rule = AuditAggregationRule(id="a1", name="test", group_by_fields=("action",))
        service.create_aggregation_rule(rule)
        result = service.aggregate_events("a1", [{"action": "login"}, {"action": "login"}])
        assert result.rule_id == "a1"
        assert result.count == 2

    def test_create_and_get_alert_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditAlertRule(id="al1", name="test-alert")
        service.create_alert_rule(rule)
        assert service.get_alert_rule("al1").name == "test-alert"

    def test_trigger_alert(self) -> None:
        service = AuditEnhancementService()
        rule = AuditAlertRule(id="al1", name="test", severity=AuditAlertSeverity.HIGH)
        service.create_alert_rule(rule)
        result = service.trigger_alert("al1", event_id="ev1")
        assert result["rule_id"] == "al1"
        assert result["severity"] == AuditAlertSeverity.HIGH
        assert result["event_id"] == "ev1"

    def test_resolve_alert(self) -> None:
        service = AuditEnhancementService()
        rule = AuditAlertRule(id="al1", name="test")
        service.create_alert_rule(rule)
        result = service.resolve_alert("al1")
        assert result["rule_id"] == "al1"

    def test_stream_config_lifecycle(self) -> None:
        service = AuditEnhancementService()
        config = AuditStreamConfig(id="s1", name="test-stream")
        service.create_stream_config(config)
        assert service.get_stream_config("s1").name == "test-stream"

        start_result = service.start_stream("s1")
        assert start_result["status"] == "started"

        stop_result = service.stop_stream("s1")
        assert stop_result["status"] == "stopped"

    def test_retention_rule(self) -> None:
        service = AuditEnhancementService()
        rule = AuditRetentionRule(id="r1", name="test-retention")
        service.create_retention_rule(rule)
        assert len(service.list_retention_rules()) == 1

    def test_notification_target(self) -> None:
        service = AuditEnhancementService()
        target = AuditNotificationTarget(
            id="n1", name="email", target_type="email", address="test@example.com"
        )
        service.create_notification_target(target)
        assert len(service.list_notification_targets()) == 1

    def test_generate_report(self) -> None:
        service = AuditEnhancementService()
        rule = AuditCorrelationRule(id="c1", name="test")
        service.create_correlation_rule(rule)
        report = service.generate_report(EnhancementType.CORRELATION)
        assert report.type == EnhancementType.CORRELATION
        assert report.rules_evaluated == 1
        assert report.rules_matched == 1


class TestHealthCheck:
    async def test_healthy(self) -> None:
        service = AuditEnhancementService()
        check = AuditEnhancementHealthCheck(service)
        report = await check.check()
        assert report.component == "audit_enhancements"
        assert report.details["enabled"] is True
        assert report.details["correlation_rules"] == 0
