"""Tests for :mod:`eaip.tenants.models`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.tenants.models import (
    BillingCategory,
    BillingLineItem,
    BillingRecord,
    BillingStatus,
    ConfigValueType,
    CrossTenantReport,
    Tenant,
    TenantConfig,
    TenantPlan,
    TenantQuota,
    TenantStatus,
    TenantUser,
    TenantUserStatus,
)


class TestTenant:
    def test_minimal(self) -> None:
        tenant = Tenant(id="t-1", name="Acme Inc", slug="acme")
        assert tenant.id == "t-1"
        assert tenant.name == "Acme Inc"
        assert tenant.slug == "acme"
        assert tenant.status is TenantStatus.ACTIVE
        assert tenant.plan is TenantPlan.FREE
        assert tenant.max_users == 10
        assert tenant.storage_limit_bytes == 1073741824

    def test_frozen(self) -> None:
        tenant = Tenant(id="t-1", name="Acme", slug="acme")
        with pytest.raises(ValueError):
            tenant.name = "Other"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            Tenant(id="t-1", name="Acme", slug="acme", unknown="x")

    def test_with_all_fields(self) -> None:
        now = datetime(2025, 1, 1)
        tenant = Tenant(
            id="t-2",
            name="Beta Corp",
            slug="beta",
            domain="beta.example.com",
            status=TenantStatus.TRIAL,
            plan=TenantPlan.ENTERPRISE,
            settings={"theme": "dark"},
            features=("audit", "analytics"),
            quotas={"users": 100, "agents": 20},
            created_at=now,
            updated_at=now,
            metadata={"region": "us-east"},
            contact_email="admin@beta.com",
            max_users=50,
            max_agents=10,
            max_workflows=25,
            storage_limit_bytes=5368709120,
        )
        assert tenant.domain == "beta.example.com"
        assert tenant.status is TenantStatus.TRIAL
        assert tenant.plan is TenantPlan.ENTERPRISE
        assert tenant.features == ("audit", "analytics")
        assert tenant.quotas == {"users": 100, "agents": 20}
        assert tenant.contact_email == "admin@beta.com"

    def test_all_statuses(self) -> None:
        for status in TenantStatus:
            tenant = Tenant(id="t-1", name="T", slug="t", status=status)
            assert tenant.status is status

    def test_all_plans(self) -> None:
        for plan in TenantPlan:
            tenant = Tenant(id="t-1", name="T", slug="t", plan=plan)
            assert tenant.plan is plan


class TestTenantUser:
    def test_minimal(self) -> None:
        user = TenantUser(id="u-1", tenant_id="t-1", email="a@b.com")
        assert user.id == "u-1"
        assert user.email == "a@b.com"
        assert user.status is TenantUserStatus.ACTIVE
        assert user.last_login is None

    def test_frozen(self) -> None:
        user = TenantUser(id="u-1", tenant_id="t-1", email="a@b.com")
        with pytest.raises(ValueError):
            user.email = "other@b.com"

    def test_with_roles_and_permissions(self) -> None:
        user = TenantUser(
            id="u-2",
            tenant_id="t-1",
            email="admin@b.com",
            name="Admin",
            roles=("admin", "billing"),
            status=TenantUserStatus.INVITED,
            permissions=("read", "write"),
        )
        assert user.name == "Admin"
        assert user.roles == ("admin", "billing")
        assert user.permissions == ("read", "write")
        assert user.status is TenantUserStatus.INVITED

    def test_all_user_statuses(self) -> None:
        for status in TenantUserStatus:
            user = TenantUser(id="u-1", tenant_id="t-1", email="a@b.com", status=status)
            assert user.status is status


class TestTenantQuota:
    def test_minimal(self) -> None:
        quota = TenantQuota(tenant_id="t-1", resource_type="agents", hard_limit=10, soft_limit=8)
        assert quota.tenant_id == "t-1"
        assert quota.resource_type == "agents"
        assert quota.hard_limit == 10
        assert quota.soft_limit == 8
        assert quota.current_usage == 0

    def test_frozen(self) -> None:
        quota = TenantQuota(tenant_id="t-1", resource_type="agents", hard_limit=10, soft_limit=8)
        with pytest.raises(ValueError):
            quota.current_usage = 5

    def test_remaining(self) -> None:
        quota = TenantQuota(
            tenant_id="t-1",
            resource_type="agents",
            hard_limit=10,
            soft_limit=8,
            current_usage=3,
            remaining=7,
        )
        assert quota.current_usage == 3
        assert quota.remaining == 7


class TestTenantConfig:
    def test_minimal(self) -> None:
        cfg = TenantConfig(id="c-1", tenant_id="t-1", category="general", key="lang")
        assert cfg.id == "c-1"
        assert cfg.type is ConfigValueType.STRING
        assert cfg.value == ""

    def test_with_all_fields(self) -> None:
        cfg = TenantConfig(
            id="c-2",
            tenant_id="t-1",
            category="security",
            key="mfa_enabled",
            value="true",
            type=ConfigValueType.BOOL,
            description="Enable MFA",
        )
        assert cfg.type is ConfigValueType.BOOL
        assert cfg.value == "true"
        assert cfg.description == "Enable MFA"

    def test_all_value_types(self) -> None:
        for vt in ConfigValueType:
            cfg = TenantConfig(id="c-1", tenant_id="t-1", category="g", key="k", type=vt)
            assert cfg.type is vt


class TestBillingLineItem:
    def test_minimal(self) -> None:
        item = BillingLineItem(description="API calls")
        assert item.quantity == 1
        assert item.unit_price == 0.0
        assert item.total == 0.0
        assert item.category is BillingCategory.OTHER

    def test_with_values(self) -> None:
        item = BillingLineItem(
            description="Agents",
            quantity=5,
            unit_price=10.0,
            total=50.0,
            category=BillingCategory.SUBSCRIPTION,
        )
        assert item.total == 50.0
        assert item.category is BillingCategory.SUBSCRIPTION


class TestBillingRecord:
    def test_minimal(self) -> None:
        now = datetime(2025, 1, 1)
        record = BillingRecord(id="inv-1", tenant_id="t-1", period_start=now, period_end=now)
        assert record.amount == 0.0
        assert record.currency == "USD"
        assert record.status is BillingStatus.PENDING
        assert record.items == ()

    def test_with_items(self) -> None:
        now = datetime(2025, 1, 1)
        items = (
            BillingLineItem(description="Item 1", total=10.0),
            BillingLineItem(description="Item 2", total=20.0),
        )
        record = BillingRecord(
            id="inv-2", tenant_id="t-1", period_start=now, period_end=now, items=items
        )
        assert len(record.items) == 2
        assert record.amount == 0.0

    def test_all_billing_statuses(self) -> None:
        now = datetime(2025, 1, 1)
        for status in BillingStatus:
            record = BillingRecord(
                id="inv-1", tenant_id="t-1", period_start=now, period_end=now, status=status
            )
            assert record.status is status


class TestCrossTenantReport:
    def test_minimal(self) -> None:
        now = datetime(2025, 1, 1)
        report = CrossTenantReport(id="r-1", period_start=now, period_end=now)
        assert report.total_tenants == 0
        assert report.active_tenants == 0

    def test_with_values(self) -> None:
        now = datetime(2025, 1, 1)
        report = CrossTenantReport(
            id="r-2",
            period_start=now,
            period_end=now,
            total_tenants=10,
            active_tenants=8,
            total_users=200,
            total_agents=15,
            total_workflows=30,
            revenue_total=5000.0,
            revenue_by_plan={"enterprise": 4000.0, "basic": 1000.0},
            usage_metrics={"api_calls": 100000},
        )
        assert report.total_tenants == 10
        assert report.active_tenants == 8
        assert report.revenue_total == 5000.0
        assert report.revenue_by_plan["enterprise"] == 4000.0
