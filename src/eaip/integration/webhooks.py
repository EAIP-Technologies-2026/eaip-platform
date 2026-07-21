"""WebhookManager — register, trigger, deliver, and verify webhooks."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from eaip.integration.events import WebhookDelivered, WebhookTriggered
from eaip.integration.exceptions import WebhookDeliveryError
from eaip.integration.models import WebhookRegistration
from eaip.logging.context import get_logger


class WebhookManager:
    def __init__(self, event_bus: Any | None = None) -> None:
        self._webhooks: dict[str, WebhookRegistration] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.integration.webhooks")

    def register_webhook(self, registration: WebhookRegistration) -> None:
        self._webhooks[registration.id] = registration
        self._log.info(
            "integration.webhook.registered", webhook_id=registration.id, name=registration.name
        )

    def unregister_webhook(self, webhook_id: str) -> WebhookRegistration | None:
        wb = self._webhooks.pop(webhook_id, None)
        if wb is not None:
            self._log.info("integration.webhook.unregistered", webhook_id=webhook_id)
        return wb

    def get_webhook(self, webhook_id: str) -> WebhookRegistration | None:
        return self._webhooks.get(webhook_id)

    async def trigger_webhook(self, webhook_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        registration = self._webhooks.get(webhook_id)
        if registration is None:
            raise WebhookDeliveryError(
                f"Webhook {webhook_id!r} not found",
                context={"webhook_id": webhook_id},
            )
        if not registration.enabled:
            raise WebhookDeliveryError(
                f"Webhook {webhook_id!r} is disabled",
                context={"webhook_id": webhook_id},
            )

        if self._event_bus is not None:
            await self._event_bus.publish(
                WebhookTriggered(
                    webhook_id=webhook_id,
                    webhook_name=registration.name,
                    payload_size=len(str(payload)),
                )
            )

        return await self.deliver_webhook(registration, payload)

    async def deliver_webhook(
        self, registration: WebhookRegistration, payload: dict[str, Any]
    ) -> dict[str, Any]:
        start = time.monotonic()
        try:
            import httpx

            headers: dict[str, str] = {"Content-Type": "application/json"}
            if registration.secret:
                body_str = str(payload)
                signature = self._compute_signature(body_str, registration.secret)
                headers["X-Webhook-Signature"] = signature

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(registration.url, json=payload, headers=headers)
                response.raise_for_status()
                duration_ms = (time.monotonic() - start) * 1000

            if self._event_bus is not None:
                await self._event_bus.publish(
                    WebhookDelivered(
                        webhook_id=registration.id,
                        webhook_name=registration.name,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )
                )

            return {"status_code": response.status_code, "duration_ms": duration_ms}
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            raise WebhookDeliveryError(
                f"Webhook delivery failed: {exc}",
                context={
                    "webhook_id": registration.id,
                    "url": registration.url,
                    "duration_ms": duration_ms,
                },
                cause=exc,
            )

    async def process_incoming_webhook(
        self, url: str, headers: dict[str, str], body: dict[str, Any]
    ) -> list[WebhookRegistration]:
        matched: list[WebhookRegistration] = []
        for wb in self._webhooks.values():
            if not wb.enabled:
                continue
            if wb.url == url:
                matched.append(wb)

        for wb in matched:
            wb = wb.model_copy(update={"call_count": wb.call_count + 1, "last_called_at": None})
            # Trigger any registered event bus subscribers
            if self._event_bus is not None:
                await self._event_bus.publish(
                    WebhookTriggered(
                        webhook_id=wb.id,
                        webhook_name=wb.name,
                        payload_size=len(str(body)),
                    )
                )

        return matched

    async def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        expected = self._compute_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def _compute_signature(payload: str, secret: str) -> str:
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


__all__ = ["WebhookManager"]
