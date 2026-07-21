"""Tests for :mod:`eaip.tenants.reporting`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.tenants.billing import BillingService
from eaip.tenants.manager import TenantManager
from eaip.tenants.models import (
    CrossTenantReport,
    Tenant,
    TenantPlan,
    TenantStatus,
    TenantUser,
)
from eaip.tenants.reporting import CrossTenantAnalytics


@pytest.fixture
def tenant_manager() -> TenantManager:
    return TenantManager()


@pytest.fixture
def billing_service() -> BillingService:
    return BillingService()


@pytest.fixture
def analytics(
    tenant_manager: TenantManager, billing_service: BillingService
) -> CrossTenantAnalytics:
    return CrossTenantAnalytics(tenant_manager, billing_service)


@pytest.fixture
def period() -> tuple[datetime, datetime]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 31, tzinfo=UTC)
    return start, end


class TestCrossTenantAnalytics:
    async def test_generate_report_empty(
        self, analytics: CrossTenantAnalytics, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        report = await analytics.generate_report(start, end)
        assert isinstance(report, CrossTenantReport)
        assert report.total_tenants == 0
        assert report.active_tenants == 0

    async def test_generate_report_with_tenants(
        self,
        analytics: CrossTenantAnalytics,
        tenant_manager: TenantManager,
        period: tuple[datetime, datetime],
    ) -> None:
        await tenant_manager.create_tenant(
            Tenant(id="t-1", name="A", slug="a", status=TenantStatus.ACTIVE)
        )
        await tenant_manager.create_tenant(
            Tenant(id="t-2", name="B", slug="b", status=TenantStatus.SUSPENDED)
        )
        start, end = period
        report = await analytics.generate_report(start, end)
        assert report.total_tenants == 2
        assert report.active_tenants == 1

    async def test_get_tenant_summary(
        self, analytics: CrossTenantAnalytics, tenant_manager: TenantManager
    ) -> None:
        await tenant_manager.create_tenant(Tenant(id="t-1", name="Acme", slug="acme"))
        summary = await analytics.get_tenant_summary("t-1")
        assert summary["tenant_id"] == "t-1"
        assert summary["name"] == "Acme"
        assert summary["status"] == "active"

    async def test_get_revenue_by_plan(
        self,
        analytics: CrossTenantAnalytics,
        tenant_manager: TenantManager,
        billing_service: BillingService,
        period: tuple[datetime, datetime],
    ) -> None:
        start, end = period
        await tenant_manager.create_tenant(
            Tenant(id="t-1", name="A", slug="a", plan=TenantPlan.ENTERPRISE)
        )
        await billing_service.record_usage_based_item("t-1", "Sub", 1, 500.0)
        invoice = await billing_service.create_invoice("t-1", start, end)
        await billing_service.mark_invoice_paid(invoice.id)
        revenue = await analytics.get_revenue_by_plan()
        assert "enterprise" in revenue
        assert revenue["enterprise"] > 0

    async def test_get_growth_metrics(
        self, analytics: CrossTenantAnalytics, tenant_manager: TenantManager
    ) -> None:
        now = datetime(2025, 6, 1, tzinfo=UTC)
        later = datetime(2025, 7, 1, tzinfo=UTC)
        old = datetime(2025, 1, 1, tzinfo=UTC)
        await tenant_manager.create_tenant(Tenant(id="t-1", name="A", slug="a", created_at=old))
        await tenant_manager.create_tenant(Tenant(id="t-2", name="B", slug="b", created_at=now))
        metrics = await analytics.get_growth_metrics(now, later)
        assert metrics["tenants_created"] == 1
        assert metrics["growth_rate"] > 0

    async def test_get_top_tenants_by_usage(
        self, analytics: CrossTenantAnalytics, tenant_manager: TenantManager
    ) -> None:
        await tenant_manager.create_tenant(Tenant(id="t-1", name="A", slug="a"))
        await tenant_manager.create_tenant(Tenant(id="t-2", name="B", slug="b"))
        u1 = TenantUser(id="u-1", tenant_id="t-1", email="a@a.com")
        u2 = TenantUser(id="u-2", tenant_id="t-1", email="b@b.com")
        u3 = TenantUser(id="u-3", tenant_id="t-2", email="c@c.com")
        await tenant_manager.add_user("t-1", u1)
        await tenant_manager.add_user("t-1", u2)
        await tenant_manager.add_user("t-2", u3)
        top = await analytics.get_top_tenants_by_usage(limit=2)
        assert len(top) == 2
        assert top[0]["tenant_id"] == "t-1"

    async def test_get_top_tenants_with_limit(
        self, analytics: CrossTenantAnalytics, tenant_manager: TenantManager
    ) -> None:
        for i in range(5):
            await tenant_manager.create_tenant(
                Tenant(id=f"t-{i + 1}", name=f"T{i + 1}", slug=f"t{i + 1}")
            )
        top = await analytics.get_top_tenants_by_usage(limit=3)
        assert len(top) == 3

    async def test_get_growth_metrics_no_data(self, analytics: CrossTenantAnalytics) -> None:
        now = datetime(2025, 6, 1, tzinfo=UTC)
        later = datetime(2025, 7, 1, tzinfo=UTC)
        metrics = await analytics.get_growth_metrics(now, later)
        assert metrics["total_tenants"] == 0
        assert metrics["growth_rate"] == 0.0

    async def test_generate_report_with_users_and_revenue(
        self,
        analytics: CrossTenantAnalytics,
        tenant_manager: TenantManager,
        billing_service: BillingService,
        period: tuple[datetime, datetime],
    ) -> None:
        start, end = period
        await tenant_manager.create_tenant(
            Tenant(id="t-1", name="A", slug="a", status=TenantStatus.ACTIVE)
        )
        u = TenantUser(id="u-1", tenant_id="t-1", email="a@a.com")
        await tenant_manager.add_user("t-1", u)
        await billing_service.record_usage_based_item("t-1", "API", 100, 0.10)
        inv = await billing_service.create_invoice("t-1", start, end)
        await billing_service.mark_invoice_paid(inv.id)
        report = await analytics.generate_report(start, end)
        assert report.total_users >= 1
        assert report.revenue_total > 0

    async def test_revenue_by_plan_no_billing_service(self) -> None:
        analytics = CrossTenantAnalytics(TenantManager())
        revenue = await analytics.get_revenue_by_plan()
        assert revenue == {}
