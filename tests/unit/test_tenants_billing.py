"""Tests for :mod:`eaip.tenants.billing`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.tenants.billing import BillingService
from eaip.tenants.exceptions import BillingError
from eaip.tenants.models import BillingStatus


@pytest.fixture
def billing() -> BillingService:
    return BillingService()


@pytest.fixture
def period() -> tuple[datetime, datetime]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 31, tzinfo=UTC)
    return start, end


class TestBillingService:
    async def test_create_invoice_empty(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        invoice = await billing.create_invoice("t-1", start, end)
        assert invoice.tenant_id == "t-1"
        assert invoice.amount == 0.0
        assert invoice.items == ()
        assert invoice.status is BillingStatus.PENDING

    async def test_record_usage_item(self, billing: BillingService) -> None:
        item = await billing.record_usage_based_item("t-1", "API calls", 1000, 0.01)
        assert item.description == "API calls"
        assert item.quantity == 1000
        assert item.unit_price == 0.01
        assert item.total == 10.0

    async def test_invoice_with_usage_items(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.record_usage_based_item("t-1", "API calls", 500, 0.01)
        await billing.record_usage_based_item("t-1", "Storage", 1, 50.0)
        invoice = await billing.create_invoice("t-1", start, end)
        assert invoice.amount == 55.0
        assert len(invoice.items) == 2

    async def test_get_invoice(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        created = await billing.create_invoice("t-1", start, end)
        fetched = await billing.get_invoice(created.id)
        assert fetched.id == created.id

    async def test_get_invoice_not_found(self, billing: BillingService) -> None:
        with pytest.raises(BillingError, match="not found"):
            await billing.get_invoice("nonexistent")

    async def test_list_invoices(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.create_invoice("t-1", start, end)
        await billing.create_invoice("t-1", start, end)
        invoices = await billing.list_invoices("t-1")
        assert len(invoices) == 2

    async def test_list_invoices_filter_by_status(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        inv1 = await billing.create_invoice("t-1", start, end)
        await billing.create_invoice("t-1", start, end)
        await billing.mark_invoice_paid(inv1.id)
        pending = await billing.list_invoices("t-1", BillingStatus.PENDING)
        paid = await billing.list_invoices("t-1", BillingStatus.PAID)
        assert len(pending) == 1
        assert len(paid) == 1

    async def test_list_invoices_empty(self, billing: BillingService) -> None:
        invoices = await billing.list_invoices("nonexistent")
        assert invoices == []

    async def test_mark_invoice_paid(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.record_usage_based_item("t-1", "Support", 1, 100.0)
        invoice = await billing.create_invoice("t-1", start, end)
        paid = await billing.mark_invoice_paid(invoice.id)
        assert paid.status is BillingStatus.PAID

    async def test_mark_invoice_paid_not_found(self, billing: BillingService) -> None:
        with pytest.raises(BillingError, match="not found"):
            await billing.mark_invoice_paid("nonexistent")

    async def test_get_tenant_usage_summary(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.record_usage_based_item("t-1", "Agents", 2, 50.0)
        invoice = await billing.create_invoice("t-1", start, end)
        await billing.mark_invoice_paid(invoice.id)
        summary = await billing.get_tenant_usage_summary("t-1", "monthly")
        assert summary["total_invoices"] == 1
        assert summary["total_billed"] == 100.0
        assert summary["paid"] == 100.0

    async def test_multiple_tenants_billing(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.record_usage_based_item("t-1", "Item", 1, 10.0)
        await billing.record_usage_based_item("t-2", "Item", 1, 20.0)
        inv1 = await billing.create_invoice("t-1", start, end)
        inv2 = await billing.create_invoice("t-2", start, end)
        assert inv1.amount == 10.0
        assert inv2.amount == 20.0

    async def test_usage_items_cleared_after_invoice(
        self, billing: BillingService, period: tuple[datetime, datetime]
    ) -> None:
        start, end = period
        await billing.record_usage_based_item("t-1", "Item", 1, 5.0)
        await billing.create_invoice("t-1", start, end)
        # Second invoice should have no items (they were cleared)
        inv2 = await billing.create_invoice("t-1", start, end)
        assert inv2.amount == 0.0
        assert inv2.items == ()
