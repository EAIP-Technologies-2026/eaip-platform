"""Audit enhancement service — correlation, enrichment, aggregation, alerts, and streaming."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.audit_enhancements.exceptions import (
    AuditAggregationError,
    AuditAlertError,
    AuditCorrelationError,
    AuditEnrichmentError,
    AuditStreamError,
)
from eaip.audit_enhancements.models import (
    AuditAggregationResult,
    AuditAggregationRule,
    AuditAlertRule,
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
from eaip.logging.context import get_logger


class AuditEnhancementService:
    def __init__(self, config: AuditEnhancementConfig | None = None) -> None:
        self._config = config or AuditEnhancementConfig()
        self._correlation_rules: dict[str, AuditCorrelationRule] = {}
        self._enrichment_rules: dict[str, AuditEnrichmentRule] = {}
        self._aggregation_rules: dict[str, AuditAggregationRule] = {}
        self._alert_rules: dict[str, AuditAlertRule] = {}
        self._notification_targets: dict[str, AuditNotificationTarget] = {}
        self._stream_configs: dict[str, AuditStreamConfig] = {}
        self._retention_rules: dict[str, AuditRetentionRule] = {}
        self._aggregation_buckets: dict[str, list[dict[str, Any]]] = {}
        self._log = get_logger("eaip.audit_enhancements.service")

    # ── configuration ──────────────────────────────────────────────────────

    @property
    def config(self) -> AuditEnhancementConfig:
        return self._config

    def update_config(self, **updates: Any) -> AuditEnhancementConfig:
        self._config = self._config.model_copy(update=updates)
        self._log.info("audit_enhancements.config.updated", config=self._config)
        return self._config

    # ── correlation ────────────────────────────────────────────────────────

    def create_correlation_rule(self, rule: AuditCorrelationRule) -> AuditCorrelationRule:
        self._correlation_rules[rule.id] = rule
        self._log.info("audit_enhancements.correlation_rule.created", rule_id=rule.id)
        return rule

    def get_correlation_rule(self, rule_id: str) -> AuditCorrelationRule:
        rule = self._correlation_rules.get(rule_id)
        if rule is None:
            raise AuditCorrelationError(f"Correlation rule {rule_id!r} not found")
        return rule

    def update_correlation_rule(self, rule_id: str, **updates: Any) -> AuditCorrelationRule:
        existing = self.get_correlation_rule(rule_id)
        updated = existing.model_copy(update=updates)
        self._correlation_rules[rule_id] = updated
        self._log.info("audit_enhancements.correlation_rule.updated", rule_id=rule_id)
        return updated

    def delete_correlation_rule(self, rule_id: str) -> None:
        if rule_id not in self._correlation_rules:
            raise AuditCorrelationError(f"Correlation rule {rule_id!r} not found")
        del self._correlation_rules[rule_id]
        self._log.info("audit_enhancements.correlation_rule.deleted", rule_id=rule_id)

    def list_correlation_rules(self) -> list[AuditCorrelationRule]:
        return list(self._correlation_rules.values())

    def correlate_events(
        self, source_ids: list[str], target_ids: list[str], rule_id: str
    ) -> AuditCorrelationResult:
        if not self._config.correlation_enabled:
            raise AuditCorrelationError("Correlation is disabled")
        rule = self.get_correlation_rule(rule_id)
        result = AuditCorrelationResult(
            rule_id=rule.id,
            source_event_ids=tuple(source_ids),
            target_event_ids=tuple(target_ids),
            correlation_id=f"corr-{rule.id}-{datetime.now(UTC).timestamp()}",
        )
        self._log.info("audit_enhancements.correlation.detected", result=result)
        return result

    # ── enrichment ─────────────────────────────────────────────────────────

    def create_enrichment_rule(self, rule: AuditEnrichmentRule) -> AuditEnrichmentRule:
        self._enrichment_rules[rule.id] = rule
        self._log.info("audit_enhancements.enrichment_rule.created", rule_id=rule.id)
        return rule

    def get_enrichment_rule(self, rule_id: str) -> AuditEnrichmentRule:
        rule = self._enrichment_rules.get(rule_id)
        if rule is None:
            raise AuditEnrichmentError(f"Enrichment rule {rule_id!r} not found")
        return rule

    def list_enrichment_rules(self) -> list[AuditEnrichmentRule]:
        return list(self._enrichment_rules.values())

    def enrich_event(
        self, event_id: str, rule_id: str, data: dict[str, Any] | None = None
    ) -> AuditEnrichmentResult:
        if not self._config.enrichment_enabled:
            raise AuditEnrichmentError("Enrichment is disabled")
        rule = self.get_enrichment_rule(rule_id)
        result = AuditEnrichmentResult(
            rule_id=rule.id,
            event_id=event_id,
            provider=rule.enrichment_providers[0] if rule.enrichment_providers else "",
            enrichment_data=data or {},
        )
        self._log.info("audit_enhancements.enrichment.applied", result=result)
        return result

    # ── aggregation ────────────────────────────────────────────────────────

    def create_aggregation_rule(self, rule: AuditAggregationRule) -> AuditAggregationRule:
        self._aggregation_rules[rule.id] = rule
        self._aggregation_buckets[rule.id] = []
        self._log.info("audit_enhancements.aggregation_rule.created", rule_id=rule.id)
        return rule

    def get_aggregation_rule(self, rule_id: str) -> AuditAggregationRule:
        rule = self._aggregation_rules.get(rule_id)
        if rule is None:
            raise AuditAggregationError(f"Aggregation rule {rule_id!r} not found")
        return rule

    def list_aggregation_rules(self) -> list[AuditAggregationRule]:
        return list(self._aggregation_rules.values())

    def aggregate_events(
        self, rule_id: str, events: list[dict[str, Any]]
    ) -> AuditAggregationResult:
        if not self._config.aggregation_enabled:
            raise AuditAggregationError("Aggregation is disabled")
        rule = self.get_aggregation_rule(rule_id)
        bucket = self._aggregation_buckets.setdefault(rule_id, [])
        bucket.extend(events)

        group_fields = rule.group_by_fields
        group_key = (
            "_".join(str(events[0].get(f, "")) for f in group_fields) if group_fields else "all"
        )

        result = AuditAggregationResult(
            rule_id=rule.id,
            group_key=group_key,
            count=len(bucket),
        )
        self._aggregation_buckets[rule_id] = []
        self._log.info("audit_enhancements.aggregation.completed", result=result)
        return result

    # ── alerts ─────────────────────────────────────────────────────────────

    def create_alert_rule(self, rule: AuditAlertRule) -> AuditAlertRule:
        self._alert_rules[rule.id] = rule
        self._log.info("audit_enhancements.alert_rule.created", rule_id=rule.id)
        return rule

    def get_alert_rule(self, rule_id: str) -> AuditAlertRule:
        rule = self._alert_rules.get(rule_id)
        if rule is None:
            raise AuditAlertError(f"Alert rule {rule_id!r} not found")
        return rule

    def list_alert_rules(self) -> list[AuditAlertRule]:
        return list(self._alert_rules.values())

    def trigger_alert(
        self, rule_id: str, event_id: str = "", details: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self._config.alerts_enabled:
            raise AuditAlertError("Alerts are disabled")
        rule = self.get_alert_rule(rule_id)
        self._log.info(
            "audit_enhancements.alert.triggered",
            rule_id=rule.id,
            severity=rule.severity,
            event_id=event_id,
        )
        return {
            "rule_id": rule.id,
            "severity": rule.severity,
            "event_id": event_id,
            "details": details or {},
        }

    def resolve_alert(self, rule_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        self.get_alert_rule(rule_id)
        self._log.info("audit_enhancements.alert.resolved", rule_id=rule_id)
        return {
            "rule_id": rule_id,
            "resolved_at": datetime.now(UTC),
            "details": details or {},
        }

    # ── notification targets ───────────────────────────────────────────────

    def create_notification_target(
        self, target: AuditNotificationTarget
    ) -> AuditNotificationTarget:
        self._notification_targets[target.id] = target
        self._log.info("audit_enhancements.notification_target.created", target_id=target.id)
        return target

    def list_notification_targets(self) -> list[AuditNotificationTarget]:
        return list(self._notification_targets.values())

    # ── streaming ──────────────────────────────────────────────────────────

    def create_stream_config(self, config: AuditStreamConfig) -> AuditStreamConfig:
        self._stream_configs[config.id] = config
        self._log.info("audit_enhancements.stream.configured", stream_id=config.id)
        return config

    def get_stream_config(self, stream_id: str) -> AuditStreamConfig:
        config = self._stream_configs.get(stream_id)
        if config is None:
            raise AuditStreamError(f"Stream config {stream_id!r} not found")
        return config

    def list_stream_configs(self) -> list[AuditStreamConfig]:
        return list(self._stream_configs.values())

    def start_stream(self, stream_id: str) -> dict[str, Any]:
        self.get_stream_config(stream_id)
        self._log.info("audit_enhancements.stream.started", stream_id=stream_id)
        return {"stream_id": stream_id, "status": "started"}

    def stop_stream(self, stream_id: str) -> dict[str, Any]:
        self.get_stream_config(stream_id)
        self._log.info("audit_enhancements.stream.stopped", stream_id=stream_id)
        return {"stream_id": stream_id, "status": "stopped"}

    # ── retention ─────────────────────────────────────────────────────────

    def create_retention_rule(self, rule: AuditRetentionRule) -> AuditRetentionRule:
        self._retention_rules[rule.id] = rule
        self._log.info("audit_enhancements.retention_rule.created", rule_id=rule.id)
        return rule

    def list_retention_rules(self) -> list[AuditRetentionRule]:
        return list(self._retention_rules.values())

    # ── reports ────────────────────────────────────────────────────────────

    def generate_report(self, report_type: EnhancementType) -> AuditEnhancementReport:
        rules: dict[str, Any] = {}
        if report_type == EnhancementType.CORRELATION:
            rules = self._correlation_rules
        elif report_type == EnhancementType.ENRICHMENT:
            rules = self._enrichment_rules
        elif report_type == EnhancementType.AGGREGATION:
            rules = self._aggregation_rules
        elif report_type == EnhancementType.ALERT:
            rules = self._alert_rules
        elif report_type == EnhancementType.STREAM:
            rules = self._stream_configs

        report = AuditEnhancementReport(
            id=f"report-{report_type.value}-{datetime.now(UTC).timestamp()}",
            type=report_type,
            rules_evaluated=len(rules),
            rules_matched=sum(1 for r in rules.values() if getattr(r, "enabled", True)),
        )
        self._log.info("audit_enhancements.report.generated", report=report)
        return report


__all__ = ["AuditEnhancementService"]
