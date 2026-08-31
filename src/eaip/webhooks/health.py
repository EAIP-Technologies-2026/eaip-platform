"""Health check for the webhook dispatcher."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.webhooks.dispatcher import WebhookDispatcher


class WebhookHealthCheck:
    """Health check for webhook dispatcher components."""

    name: str = "webhooks"

    def __init__(self, dispatcher: WebhookDispatcher) -> None:
        self._dispatcher = dispatcher

    async def check(self) -> HealthReport:
        endpoints = self._dispatcher.list_endpoints()
        deliveries = await self._dispatcher.list_deliveries()
        queue_depth = await self._dispatcher.retry_queue.get_queue_depth()
        failed_count = len([d for d in deliveries if d.status.value == "failed"])
        retrying_count = len([d for d in deliveries if d.status.value == "retrying"])

        details = {
            "endpoints_total": len(endpoints),
            "endpoints_active": len([e for e in endpoints if e.status.value == "active"]),
            "deliveries_total": len(deliveries),
            "deliveries_failed": failed_count,
            "deliveries_retrying": retrying_count,
            "retry_queue_depth": queue_depth,
        }
        status = HealthStatus.HEALTHY
        message = "Webhook dispatcher is operational"
        if failed_count > 10:
            status = HealthStatus.DEGRADED
            message = f"{failed_count} failed webhook deliveries"
        if retrying_count > 20:
            status = HealthStatus.DEGRADED
            message = f"{retrying_count} deliveries in retry queue"

        return HealthReport(
            component="webhooks",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["WebhookHealthCheck"]
