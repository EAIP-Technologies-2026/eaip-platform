"""Cross-tenant analytics — reports, summaries, revenue, and growth metrics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from eaip.tenants.models import CrossTenantReport, TenantStatus

if TYPE_CHECKING:
    from eaip.tenants.billing import BillingService
    from eaip.tenants.manager import TenantManager


class CrossTenantAnalytics:
    """Aggregates data across all tenants for reporting and analytics."""

    def __init__(
        self,
        tenant_manager: TenantManager,
        billing_service: BillingService | None = None,
    ) -> None:
        self._tenant_manager = tenant_manager
        self._billing_service = billing_service

    async def generate_report(
        self, period_start: datetime, period_end: datetime
    ) -> CrossTenantReport:
        """Generate a cross-tenant report for the given period."""
        all_tenants = await self._tenant_manager.list_tenants()
        active_tenants = [t for t in all_tenants if t.status is TenantStatus.ACTIVE]

        total_users = 0
        total_agents = 0
        total_workflows = 0
        for tenant in all_tenants:
            total_agents += tenant.max_agents if tenant.status is TenantStatus.ACTIVE else 0
            total_workflows += tenant.max_workflows if tenant.status is TenantStatus.ACTIVE else 0
            try:
                users = await self._tenant_manager.list_users(tenant.id)
                total_users += len(users)
            except Exception:
                pass

        revenue_total = 0.0
        revenue_by_plan: dict[str, float] = {}
        if self._billing_service is not None:
            for tenant in active_tenants:
                summary = await self._billing_service.get_tenant_usage_summary(
                    tenant.id, f"{period_start.isoformat()}/{period_end.isoformat()}"
                )
                revenue_total += summary["paid"]
                plan = tenant.plan.value
                revenue_by_plan[plan] = revenue_by_plan.get(plan, 0.0) + summary["paid"]

        usage_metrics: dict[str, Any] = {
            "total_tenants": len(all_tenants),
            "active_tenants": len(active_tenants),
            "total_users": total_users,
            "total_agents": total_agents,
            "total_workflows": total_workflows,
        }

        return CrossTenantReport(
            id=f"report-{period_start.strftime('%Y%m')}-{len(all_tenants)}",
            period_start=period_start,
            period_end=period_end,
            total_tenants=len(all_tenants),
            active_tenants=len(active_tenants),
            total_users=total_users,
            total_agents=total_agents,
            total_workflows=total_workflows,
            revenue_total=revenue_total,
            revenue_by_plan=revenue_by_plan,
            usage_metrics=usage_metrics,
        )

    async def get_tenant_summary(self, tenant_id: str) -> dict[str, Any]:
        """Get a summary for a single tenant."""
        tenant = await self._tenant_manager.get_tenant(tenant_id)
        users = await self._tenant_manager.list_users(tenant_id)
        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "status": tenant.status.value,
            "plan": tenant.plan.value,
            "user_count": len(users),
            "features": list(tenant.features),
            "created_at": tenant.created_at.isoformat(),
        }

    async def get_revenue_by_plan(self) -> dict[str, float]:
        """Get revenue breakdown by plan across all tenants."""
        result: dict[str, float] = {}
        if self._billing_service is None:
            return result
        all_tenants = await self._tenant_manager.list_tenants()
        for tenant in all_tenants:
            summary = await self._billing_service.get_tenant_usage_summary(tenant.id, "all")
            plan = tenant.plan.value
            result[plan] = result.get(plan, 0.0) + summary.get("paid", 0)
        return result

    async def get_growth_metrics(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get tenant growth metrics between two dates."""
        all_tenants = await self._tenant_manager.list_tenants()
        total = len(all_tenants)
        active = len([t for t in all_tenants if t.status is TenantStatus.ACTIVE])

        created_in_period = sum(1 for t in all_tenants if start_date <= t.created_at <= end_date)
        closed_in_period = sum(
            1
            for t in all_tenants
            if t.status is TenantStatus.CLOSED and start_date <= t.updated_at <= end_date
        )

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_tenants": total,
            "active_tenants": active,
            "tenants_created": created_in_period,
            "tenants_closed": closed_in_period,
            "growth_rate": round((created_in_period / max(total, 1)) * 100, 2),
            "churn_rate": round((closed_in_period / max(total, 1)) * 100, 2),
        }

    async def get_top_tenants_by_usage(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top tenants by usage metrics."""
        all_tenants = await self._tenant_manager.list_tenants()
        top: list[dict[str, Any]] = []
        for tenant in all_tenants:
            try:
                users = await self._tenant_manager.list_users(tenant.id)
                top.append(
                    {
                        "tenant_id": tenant.id,
                        "name": tenant.name,
                        "status": tenant.status.value,
                        "plan": tenant.plan.value,
                        "user_count": len(users),
                        "max_agents": tenant.max_agents,
                        "max_workflows": tenant.max_workflows,
                    }
                )
            except Exception:
                pass
        top.sort(key=lambda x: x["user_count"], reverse=True)
        return top[:limit]
