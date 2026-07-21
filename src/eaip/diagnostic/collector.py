"""DiagnosticCollector — collect, store, and manage diagnostic reports."""

from __future__ import annotations

from eaip.diagnostic.events import ReportCollected, RuleCreated, RuleUpdated
from eaip.diagnostic.exceptions import ReportNotFoundError
from eaip.diagnostic.models import CollectionRule, CollectorConfig, DiagnosticReport
from eaip.logging.context import get_logger


class DiagnosticCollector:
    """Central service for collecting and managing diagnostic data."""

    def __init__(self, config: CollectorConfig | None = None) -> None:
        self._config = config or CollectorConfig()
        self._reports: dict[str, DiagnosticReport] = {}
        self._rules: dict[str, CollectionRule] = {}
        self._log = get_logger("eaip.diagnostic.collector")

    @property
    def config(self) -> CollectorConfig:
        return self._config

    async def collect_report(self, report: DiagnosticReport) -> DiagnosticReport:
        """Store a new diagnostic report."""
        if len(self._reports) >= self._config.max_reports:
            self._log.warning(
                "diagnostic.report.limit_reached", max_reports=self._config.max_reports
            )
        self._reports[report.id] = report
        ReportCollected(
            report_id=report.id,
            component=report.component,
            category=report.category,
            severity=report.severity.value,
        )
        self._log.info(
            "diagnostic.report.collected", report_id=report.id, component=report.component
        )
        return report

    async def get_report(self, report_id: str) -> DiagnosticReport:
        """Get a diagnostic report by ID."""
        report = self._reports.get(report_id)
        if report is None:
            raise ReportNotFoundError(f"Diagnostic report not found: {report_id}")
        return report

    async def list_reports(
        self,
        component: str | None = None,
        category: str | None = None,
        severity: str | None = None,
    ) -> list[DiagnosticReport]:
        """List diagnostic reports, optionally filtered."""
        result = list(self._reports.values())
        if component is not None:
            result = [r for r in result if r.component == component]
        if category is not None:
            result = [r for r in result if r.category == category]
        if severity is not None:
            result = [r for r in result if r.severity.value == severity]
        return sorted(result, key=lambda r: r.collected_at, reverse=True)

    async def create_rule(self, rule: CollectionRule) -> CollectionRule:
        """Create a new collection rule."""
        self._rules[rule.id] = rule
        RuleCreated(
            rule_id=rule.id,
            name=rule.name,
            component=rule.component,
            metric_path=rule.metric_path,
        )
        self._log.info("diagnostic.rule.created", rule_id=rule.id, name=rule.name)
        return rule

    async def update_rule(self, rule_id: str, enabled: bool) -> CollectionRule:
        """Update a collection rule's enabled state."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise ReportNotFoundError(f"Collection rule not found: {rule_id}")
        updated = rule.model_copy(update={"enabled": enabled})
        self._rules[rule_id] = updated
        RuleUpdated(
            rule_id=rule_id,
            name=rule.name,
            enabled=enabled,
        )
        self._log.info("diagnostic.rule.updated", rule_id=rule_id, enabled=enabled)
        return updated

    async def get_rule(self, rule_id: str) -> CollectionRule:
        """Get a collection rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise ReportNotFoundError(f"Collection rule not found: {rule_id}")
        return rule

    async def list_rules(self, component: str | None = None) -> list[CollectionRule]:
        """List collection rules, optionally filtered."""
        result = list(self._rules.values())
        if component is not None:
            result = [r for r in result if r.component == component]
        return sorted(result, key=lambda r: r.name)

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about collected reports and rules."""
        return {
            "total_reports": len(self._reports),
            "total_rules": len(self._rules),
            "active_rules": sum(1 for r in self._rules.values() if r.enabled),
        }


__all__ = ["DiagnosticCollector"]
