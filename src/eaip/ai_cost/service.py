"""AiCostService — cost tracking, budgets, optimization, reports, projections for AI model costs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from eaip.ai_cost.events import (
    AiCostAllocationUpdated,
    AiCostAnomalyDetected,
    AiCostBudgetAlertTriggered,
    AiCostBudgetCreated,
    AiCostBudgetExceeded,
    AiCostBudgetUpdated,
    AiCostDashboardUpdated,
    AiCostOptimizationApplied,
    AiCostOptimizationRuleCreated,
    AiCostProjectionComputed,
    AiCostRecorded,
    AiCostReportGenerated,
    ModelCostRateUpdated,
)
from eaip.ai_cost.exceptions import (
    AiCostBudgetError,
    AiCostOptimizationError,
    AiCostRecordError,
    AiCostReportError,
)
from eaip.ai_cost.models import (
    AiCostAlert,
    AiCostAllocation,
    AiCostBudget,
    AiCostConfig,
    AiCostDashboard,
    AiCostOptimizationRule,
    AiCostProjection,
    AiCostRecord,
    AiCostReport,
    AiCostReportPeriod,
    CostType,
    ModelCostRate,
    TokenCostBreakdown,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AiCostService:
    """Central service for tracking, budgeting, optimizing, and reporting AI model costs."""

    def __init__(self, config: AiCostConfig | None = None) -> None:
        self._config = config or AiCostConfig()
        self._records: dict[str, AiCostRecord] = {}
        self._budgets: dict[str, AiCostBudget] = {}
        self._alerts: dict[str, AiCostAlert] = {}
        self._rules: dict[str, AiCostOptimizationRule] = {}
        self._reports: dict[str, AiCostReport] = {}
        self._projections: dict[str, AiCostProjection] = {}
        self._allocations: dict[str, AiCostAllocation] = {}
        self._cost_rates: dict[str, ModelCostRate] = {}
        self._event_callbacks: list[Any] = []
        self._log = get_logger("eaip.ai_cost.service")

    @property
    def config(self) -> AiCostConfig:
        return self._config

    def set_event_callback(self, callback: Any) -> None:
        self._event_callbacks.append(callback)

    def _emit(self, event: Any) -> None:
        for cb in self._event_callbacks:
            cb(event)

    # ── Cost Tracking ──────────────────────────────────────────────────────────

    async def record_cost(
        self,
        model_id: str,
        cost_type: CostType,
        amount: float,
        currency: str = "USD",
        tenant_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> AiCostRecord:
        rate = self._cost_rates.get(model_id)
        token_breakdown: TokenCostBreakdown | None = None
        if rate is not None and (input_tokens > 0 or output_tokens > 0):
            token_breakdown = TokenCostBreakdown(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_cost=(input_tokens / 1000) * rate.input_cost_per_1k_tokens,
                output_cost=(output_tokens / 1000) * rate.output_cost_per_1k_tokens,
                currency=currency,
            )

        record = AiCostRecord(
            id=f"cr_{utc_now().timestamp():.0f}_{model_id}",
            model_id=model_id,
            cost_type=cost_type,
            amount=amount,
            currency=currency,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tags=tags,
            metadata=metadata or {},
            token_breakdown=token_breakdown,
        )
        self._records[record.id] = record
        self._log.info("ai_cost.recorded", model_id=model_id, amount=amount)

        event = AiCostRecorded(
            record_id=record.id,
            model_id=model_id,
            cost_type=cost_type.value,
            amount=amount,
            currency=currency,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._emit(event)
        await self._check_budgets(record)
        return record

    async def get_record(self, record_id: str) -> AiCostRecord:
        record = self._records.get(record_id)
        if record is None:
            raise AiCostRecordError(f"cost record not found: {record_id!r}")
        return record

    async def query_costs(
        self,
        model_id: str | None = None,
        tenant_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[AiCostRecord]:
        results = list(self._records.values())
        if model_id:
            results = [r for r in results if r.model_id == model_id]
        if tenant_id:
            results = [r for r in results if r.tenant_id == tenant_id]
        if start:
            results = [r for r in results if r.timestamp >= start]
        if end:
            results = [r for r in results if r.timestamp <= end]
        return results

    # ── Cost Rates ─────────────────────────────────────────────────────────────

    async def upsert_cost_rate(self, rate: ModelCostRate) -> ModelCostRate:
        self._cost_rates[rate.model_id] = rate
        self._log.info("ai_cost.cost_rate.upserted", model_id=rate.model_id)
        event = ModelCostRateUpdated(
            model_id=rate.model_id,
            provider=rate.provider,
            input_cost_per_1k_tokens=rate.input_cost_per_1k_tokens,
            output_cost_per_1k_tokens=rate.output_cost_per_1k_tokens,
            currency=rate.currency,
        )
        self._emit(event)
        return rate

    async def get_cost_rate(self, model_id: str) -> ModelCostRate | None:
        return self._cost_rates.get(model_id)

    # ── Budgets ────────────────────────────────────────────────────────────────

    async def create_budget(self, budget: AiCostBudget) -> AiCostBudget:
        self._budgets[budget.id] = budget
        self._log.info("ai_cost.budget.created", budget_id=budget.id, name=budget.name)

        event = AiCostBudgetCreated(
            budget_id=budget.id,
            name=budget.name,
            amount=budget.amount,
            currency=budget.currency,
            period=budget.period.value,
            model_id=budget.model_id,
        )
        self._emit(event)
        return budget

    async def update_budget(self, budget_id: str, **updates: Any) -> AiCostBudget:
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise AiCostBudgetError(f"budget not found: {budget_id!r}")
        updated = budget.model_copy(update=updates)
        self._budgets[budget_id] = updated
        self._log.info("ai_cost.budget.updated", budget_id=budget_id)

        event = AiCostBudgetUpdated(budget_id=budget_id, updates=updates)
        self._emit(event)
        return updated

    async def get_budget(self, budget_id: str) -> AiCostBudget:
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise AiCostBudgetError(f"budget not found: {budget_id!r}")
        return budget

    async def list_budgets(self) -> list[AiCostBudget]:
        return list(self._budgets.values())

    async def get_current_spend_for_budget(self, budget_id: str) -> float:
        budget = await self.get_budget(budget_id)
        records = [
            r for r in self._records.values() if budget.start_date <= r.timestamp <= budget.end_date
        ]
        if budget.model_id:
            records = [r for r in records if r.model_id == budget.model_id]
        return sum(r.amount for r in records)

    async def _check_budgets(self, record: AiCostRecord) -> None:
        for budget in self._budgets.values():
            if not budget.enabled:
                continue
            if budget.model_id and record.model_id != budget.model_id:
                continue
            if not (budget.start_date <= record.timestamp <= budget.end_date):
                continue

            current_spend = await self.get_current_spend_for_budget(budget.id)

            for threshold in budget.alert_thresholds:
                if current_spend >= budget.amount * threshold:
                    alert = AiCostAlert(
                        id=f"alert_{utc_now().timestamp():.0f}",
                        budget_id=budget.id,
                        threshold=threshold,
                        actual_spend=current_spend,
                        budgeted_amount=budget.amount,
                        percentage=current_spend / budget.amount if budget.amount > 0 else 0.0,
                    )
                    self._alerts[alert.id] = alert

                    self._emit(
                        AiCostBudgetAlertTriggered(
                            alert_id=alert.id,
                            budget_id=budget.id,
                            threshold=threshold,
                            actual_spend=current_spend,
                            percentage=alert.percentage,
                        )
                    )

            if current_spend >= budget.amount:
                self._emit(
                    AiCostBudgetExceeded(
                        budget_id=budget.id,
                        actual_spend=current_spend,
                        budgeted_amount=budget.amount,
                        overshoot=current_spend - budget.amount,
                    )
                )

    # ── Optimization Rules ─────────────────────────────────────────────────────

    async def create_optimization_rule(
        self,
        rule: AiCostOptimizationRule,
    ) -> AiCostOptimizationRule:
        self._rules[rule.id] = rule
        self._log.info("ai_cost.optimization_rule.created", rule_id=rule.id, name=rule.name)

        event = AiCostOptimizationRuleCreated(
            rule_id=rule.id,
            name=rule.name,
            strategy=rule.strategy.value,
            model_id=rule.model_id,
        )
        self._emit(event)
        return rule

    async def list_optimization_rules(self) -> list[AiCostOptimizationRule]:
        return list(self._rules.values())

    async def apply_optimization(self, rule_id: str, model_id: str) -> dict[str, Any]:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise AiCostOptimizationError(f"optimization rule not found: {rule_id!r}")

        model_records = [r for r in self._records.values() if r.model_id == model_id]
        current_cost = sum(r.amount for r in model_records) if model_records else 0.0
        estimated_savings = current_cost * 0.15

        event = AiCostOptimizationApplied(
            rule_id=rule_id,
            model_id=model_id,
            estimated_savings=estimated_savings,
            currency="USD",
        )
        self._emit(event)

        return {
            "rule_id": rule_id,
            "model_id": model_id,
            "estimated_savings": estimated_savings,
            "currency": "USD",
        }

    # ── Reports ────────────────────────────────────────────────────────────────

    async def generate_report(
        self,
        period: AiCostReportPeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> AiCostReport:
        records = [r for r in self._records.values() if period_start <= r.timestamp <= period_end]

        total_cost = sum(r.amount for r in records)
        cost_by_model: dict[str, float] = defaultdict(float)
        cost_by_type: dict[str, float] = defaultdict(float)
        cost_by_tenant: dict[str, float] = defaultdict(float)
        total_input_tokens = sum(r.input_tokens for r in records)
        total_output_tokens = sum(r.output_tokens for r in records)

        for r in records:
            cost_by_model[r.model_id] += r.amount
            cost_by_type[r.cost_type.value] += r.amount
            if r.tenant_id:
                cost_by_tenant[r.tenant_id] += r.amount

        report = AiCostReport(
            id=f"rpt_{utc_now().timestamp():.0f}",
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_cost=total_cost,
            cost_by_model=dict(cost_by_model),
            cost_by_type=dict(cost_by_type),
            cost_by_tenant=dict(cost_by_tenant),
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
        )
        self._reports[report.id] = report
        self._log.info("ai_cost.report.generated", report_id=report.id, total_cost=total_cost)

        event = AiCostReportGenerated(
            report_id=report.id,
            period=period.value,
            period_start=period_start,
            period_end=period_end,
            total_cost=total_cost,
        )
        self._emit(event)
        return report

    async def get_report(self, report_id: str) -> AiCostReport:
        report = self._reports.get(report_id)
        if report is None:
            raise AiCostReportError(f"report not found: {report_id!r}")
        return report

    # ── Projections ────────────────────────────────────────────────────────────

    async def compute_projection(
        self,
        model_id: str | None = None,
        horizon_days: int | None = None,
    ) -> AiCostProjection:
        days = horizon_days or self._config.projection_horizon_days

        records = list(self._records.values())
        if model_id:
            records = [r for r in records if r.model_id == model_id]

        if not records:
            projection = AiCostProjection(
                id=f"proj_{utc_now().timestamp():.0f}",
                model_id=model_id,
                projected_amount=0.0,
                confidence_interval_low=0.0,
                confidence_interval_high=0.0,
                projection_start=utc_now(),
                projection_end=utc_now() + timedelta(days=days),
                historical_data_points=0,
            )
        else:
            avg_daily = sum(r.amount for r in records) / max(
                (max(r.timestamp for r in records) - min(r.timestamp for r in records)).days or 1, 1
            )
            projected = avg_daily * days
            projection = AiCostProjection(
                id=f"proj_{utc_now().timestamp():.0f}",
                model_id=model_id,
                projected_amount=round(projected, 4),
                confidence_interval_low=round(projected * 0.8, 4),
                confidence_interval_high=round(projected * 1.2, 4),
                projection_start=utc_now(),
                projection_end=utc_now() + timedelta(days=days),
                historical_data_points=len(records),
            )

        self._projections[projection.id] = projection

        event = AiCostProjectionComputed(
            projection_id=projection.id,
            model_id=model_id,
            projected_amount=projection.projected_amount,
            projection_start=projection.projection_start,
            projection_end=projection.projection_end,
        )
        self._emit(event)
        return projection

    async def get_projection(self, projection_id: str) -> AiCostProjection:
        projection = self._projections.get(projection_id)
        if projection is None:
            raise AiCostReportError(f"projection not found: {projection_id!r}")
        return projection

    # ── Allocations ────────────────────────────────────────────────────────────

    async def create_allocation(self, allocation: AiCostAllocation) -> AiCostAllocation:
        self._allocations[allocation.id] = allocation
        self._log.info("ai_cost.allocation.created", allocation_id=allocation.id)

        event = AiCostAllocationUpdated(
            allocation_id=allocation.id,
            tenant_id=allocation.tenant_id,
            amount=allocation.amount,
            currency=allocation.currency,
            period_start=allocation.period_start,
            period_end=allocation.period_end,
        )
        self._emit(event)
        return allocation

    async def list_allocations(self, tenant_id: str | None = None) -> list[AiCostAllocation]:
        if tenant_id:
            return [a for a in self._allocations.values() if a.tenant_id == tenant_id]
        return list(self._allocations.values())

    # ── Anomalies ──────────────────────────────────────────────────────────────

    async def detect_anomalies(
        self, model_id: str, current_cost: float, expected_cost: float
    ) -> dict[str, Any]:
        deviation = current_cost - expected_cost
        pct = (deviation / expected_cost * 100) if expected_cost > 0 else 0.0

        critical_pct = 50
        high_pct = 25
        medium_pct = 10

        severity = "low"
        if abs(pct) > critical_pct:
            severity = "critical"
        elif abs(pct) > high_pct:
            severity = "high"
        elif abs(pct) > medium_pct:
            severity = "medium"

        event = AiCostAnomalyDetected(
            model_id=model_id,
            actual_cost=current_cost,
            expected_cost=expected_cost,
            deviation=deviation,
            severity=severity,
        )
        self._emit(event)

        return {
            "model_id": model_id,
            "actual_cost": current_cost,
            "expected_cost": expected_cost,
            "deviation": deviation,
            "severity": severity,
        }

    # ── Dashboard ──────────────────────────────────────────────────────────────

    async def get_dashboard(self) -> AiCostDashboard:
        total_spend = sum(r.amount for r in self._records.values())
        model_totals: dict[str, float] = defaultdict(float)
        for r in self._records.values():
            model_totals[r.model_id] += r.amount
        top_models = tuple(
            m for m, _ in sorted(model_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        active_alert_count = len(self._alerts)
        total_budget_amount = sum(b.amount for b in self._budgets.values() if b.enabled)
        budget_remaining = max(0.0, total_budget_amount - total_spend)

        latest_projection = None
        if self._projections:
            latest_projection = max(self._projections.values(), key=lambda p: p.computed_at)
        projected = latest_projection.projected_amount if latest_projection else 0.0

        dashboard = AiCostDashboard(
            id="main",
            name="AI Cost Dashboard",
            current_spend=total_spend,
            budget_remaining=budget_remaining,
            projected_cost=projected,
            active_alerts=active_alert_count,
            top_models=top_models,
        )

        event = AiCostDashboardUpdated(
            dashboard_id=dashboard.id,
            current_spend=total_spend,
            projected_cost=projected,
            active_alerts=active_alert_count,
        )
        self._emit(event)
        return dashboard


__all__ = ["AiCostService"]
