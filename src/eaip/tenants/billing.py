"""Billing service — invoice generation, usage recording, and payment tracking."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from eaip.logging.context import get_logger
from eaip.tenants.events import InvoiceCreated, InvoicePaid
from eaip.tenants.exceptions import BillingError
from eaip.tenants.models import (
    BillingCategory,
    BillingLineItem,
    BillingRecord,
    BillingStatus,
)

if TYPE_CHECKING:
    from eaip.events.bus import EventBus


class BillingService:
    """Manages tenant billing — invoices, usage items, and payment recording."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._log = get_logger("eaip.tenants.billing")
        self._invoices: dict[str, BillingRecord] = {}
        self._usage_items: dict[str, list[BillingLineItem]] = {}

    async def create_invoice(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> BillingRecord:
        """Generate an invoice for a tenant covering the given period.

        Aggregates any recorded usage items for the tenant.
        """
        invoice_id = f"inv-{tenant_id}-{period_start.strftime('%Y%m')}-{len(self._invoices) + 1}"
        items = tuple(self._usage_items.pop(tenant_id, []))
        total = sum(item.total for item in items)

        invoice = BillingRecord(
            id=invoice_id,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            amount=total,
            items=items,
        )
        self._invoices[invoice_id] = invoice

        if self._event_bus is not None:
            await self._event_bus.publish(
                InvoiceCreated(
                    invoice_id=invoice_id,
                    tenant_id=tenant_id,
                    period_start=period_start,
                    period_end=period_end,
                    amount=total,
                )
            )
        self._log.info("billing.invoice_created", invoice_id=invoice_id, amount=total)
        return invoice

    async def record_usage_based_item(
        self,
        tenant_id: str,
        description: str,
        quantity: int,
        unit_price: float,
    ) -> BillingLineItem:
        """Record a usage-based billing item for a tenant."""
        total = round(quantity * unit_price, 2)
        item = BillingLineItem(
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            total=total,
            category=BillingCategory.USAGE,
        )
        if tenant_id not in self._usage_items:
            self._usage_items[tenant_id] = []
        self._usage_items[tenant_id].append(item)
        self._log.info("billing.usage_recorded", tenant_id=tenant_id, total=total)
        return item

    async def get_invoice(self, invoice_id: str) -> BillingRecord:
        """Get an invoice by ID.

        Raises:
            BillingError: If the invoice is not found.
        """
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise BillingError(f"Invoice {invoice_id!r} not found")
        return invoice

    async def list_invoices(
        self, tenant_id: str, status: BillingStatus | None = None
    ) -> list[BillingRecord]:
        """List invoices for a tenant, optionally filtered by status."""
        results = [inv for inv in self._invoices.values() if inv.tenant_id == tenant_id]
        if status is not None:
            results = [inv for inv in results if inv.status is status]
        return results

    async def mark_invoice_paid(self, invoice_id: str) -> BillingRecord:
        """Mark an invoice as paid.

        Raises:
            BillingError: If the invoice is not found.
        """
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise BillingError(f"Invoice {invoice_id!r} not found")
        updated = invoice.model_copy(update={"status": BillingStatus.PAID})
        self._invoices[invoice_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                InvoicePaid(
                    invoice_id=invoice_id,
                    tenant_id=invoice.tenant_id,
                    amount=invoice.amount,
                )
            )
        self._log.info("billing.invoice_paid", invoice_id=invoice_id)
        return updated

    async def get_tenant_usage_summary(self, tenant_id: str, period: str) -> dict[str, Any]:
        """Get a usage summary for a tenant over a given period.

        Returns:
            A dictionary with summary metrics.
        """
        tenant_invoices = [inv for inv in self._invoices.values() if inv.tenant_id == tenant_id]
        total_billed = sum(inv.amount for inv in tenant_invoices)
        pending = sum(inv.amount for inv in tenant_invoices if inv.status is BillingStatus.PENDING)
        paid = sum(inv.amount for inv in tenant_invoices if inv.status is BillingStatus.PAID)
        return {
            "tenant_id": tenant_id,
            "period": period,
            "total_invoices": len(tenant_invoices),
            "total_billed": total_billed,
            "pending": pending,
            "paid": paid,
            "currency": "USD",
        }
