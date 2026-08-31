"""Webhook dispatcher — endpoint management, delivery, retry, and tracking."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.webhooks.events import (
    EndpointRegistered,
    EndpointUpdated,
    WebhookDelivered,
    WebhookDeliveryFailed,
    WebhookRetrying,
)
from eaip.webhooks.exceptions import (
    DeliveryError,
    EndpointNotFoundError,
)
from eaip.webhooks.models import (
    DeliveryReceipt,
    DeliveryStatus,
    WebhookConfig,
    WebhookDelivery,
    WebhookEndpoint,
)
from eaip.webhooks.retry import RetryQueueService
from eaip.webhooks.signing import SignatureService


class WebhookDispatcher:
    """Manages webhook endpoints and dispatches event payloads with retry and signing."""

    def __init__(
        self,
        config: WebhookConfig | None = None,
        signature_service: SignatureService | None = None,
        retry_queue: RetryQueueService | None = None,
    ) -> None:
        self._config = config or WebhookConfig()
        self._signature_service = signature_service or SignatureService()
        self._retry_queue = retry_queue or RetryQueueService(config=self._config)
        self._endpoints: dict[str, WebhookEndpoint] = {}
        self._deliveries: dict[str, WebhookDelivery] = {}
        self._receipts: dict[str, DeliveryReceipt] = {}
        self._events: list[Any] = []
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._log = get_logger("eaip.webhooks.dispatcher")

    @property
    def config(self) -> WebhookConfig:
        return self._config

    @property
    def signature_service(self) -> SignatureService:
        return self._signature_service

    @property
    def retry_queue(self) -> RetryQueueService:
        return self._retry_queue

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._config.default_timeout_seconds)
            )
        return self._client

    def _ensure_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._config.max_concurrent_deliveries)
        return self._semaphore

    # -- Endpoint management -------------------------------------------------

    def register(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        self._endpoints[endpoint.id] = endpoint
        self._events.append(
            EndpointRegistered(
                endpoint_id=endpoint.id,
                name=endpoint.name,
                url=endpoint.url,
            )
        )
        return endpoint

    def update(self, endpoint_id: str, **updates: Any) -> WebhookEndpoint:
        existing = self._endpoints.get(endpoint_id)
        if existing is None:
            raise EndpointNotFoundError(f"Endpoint '{endpoint_id}' not found")
        updated = existing.model_copy(update={**updates, "updated_at": utc_now()})
        self._endpoints[endpoint_id] = updated
        self._events.append(
            EndpointUpdated(
                endpoint_id=updated.id,
                name=updated.name,
                url=updated.url,
            )
        )
        return updated

    def get(self, endpoint_id: str) -> WebhookEndpoint:
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint '{endpoint_id}' not found")
        return endpoint

    def delete(self, endpoint_id: str) -> bool:
        if endpoint_id not in self._endpoints:
            raise EndpointNotFoundError(f"Endpoint '{endpoint_id}' not found")
        del self._endpoints[endpoint_id]
        return True

    def list_endpoints(self) -> list[WebhookEndpoint]:
        return list(self._endpoints.values())

    # -- Delivery -------------------------------------------------------------

    async def deliver(
        self, webhook_id: str, event_type: str, payload: dict[str, Any]
    ) -> WebhookDelivery:
        endpoint = self.get(webhook_id)
        return await self.deliver_payload(endpoint, event_type, payload)

    async def deliver_payload(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict[str, Any],
    ) -> WebhookDelivery:
        if not endpoint.enabled or endpoint.status.value != "active":
            raise DeliveryError(f"Endpoint '{endpoint.id}' is not active")

        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            endpoint_id=endpoint.id,
            event_type=event_type,
            payload=payload,
            status=DeliveryStatus.PENDING,
            attempt=1,
            max_attempts=endpoint.retry_config.get(
                "max_attempts", self._config.default_max_attempts
            ),
        )
        self._deliveries[delivery.id] = delivery

        sem = self._ensure_semaphore()
        async with sem:
            return await self._send(delivery, endpoint)

    async def _send(self, delivery: WebhookDelivery, endpoint: WebhookEndpoint) -> WebhookDelivery:
        client = self._ensure_client()
        headers: dict[str, str] = dict(endpoint.headers)

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        headers["X-Event-Type"] = delivery.event_type
        headers["X-Delivery-Id"] = delivery.id

        secret = endpoint.secret
        if not secret:
            active = await self._signature_service.get_active_secret(endpoint.id)
            if active is not None:
                secret = active.key

        if secret:
            signature = await self._signature_service.sign_payload(delivery.payload, secret)
            headers[self._config.signature_header_name] = signature

        start = time.monotonic()
        try:
            response = await client.post(
                endpoint.url,
                json=delivery.payload,
                headers=headers,
                timeout=endpoint.timeout_seconds,
            )
            duration_ms = (time.monotonic() - start) * 1000
            body = await response.aread()
            body_text = body.decode("utf-8", errors="replace")[:4096]

            if response.is_success:
                delivery = delivery.model_copy(
                    update={
                        "status": DeliveryStatus.DELIVERED,
                        "response_status_code": response.status_code,
                        "response_body": body_text,
                        "duration_ms": duration_ms,
                        "delivered_at": utc_now(),
                        "last_attempt_at": utc_now(),
                    }
                )
                self._deliveries[delivery.id] = delivery
                self._events.append(
                    WebhookDelivered(
                        delivery_id=delivery.id,
                        endpoint_id=endpoint.id,
                        event_type_name=delivery.event_type,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )
                )
                self._record_receipt(delivery, headers, response.status_code, duration_ms)
            else:
                delivery = delivery.model_copy(
                    update={
                        "response_status_code": response.status_code,
                        "response_body": body_text,
                        "duration_ms": duration_ms,
                        "last_attempt_at": utc_now(),
                    }
                )
                delivery = await self._handle_failure(
                    delivery, endpoint, f"HTTP {response.status_code}: {body_text[:200]}"
                )
        except httpx.TimeoutException as exc:
            duration_ms = (time.monotonic() - start) * 1000
            delivery = delivery.model_copy(
                update={"duration_ms": duration_ms, "last_attempt_at": utc_now()}
            )
            delivery = await self._handle_failure(delivery, endpoint, f"timeout: {exc}")
        except httpx.RequestError as exc:
            duration_ms = (time.monotonic() - start) * 1000
            delivery = delivery.model_copy(
                update={"duration_ms": duration_ms, "last_attempt_at": utc_now()}
            )
            delivery = await self._handle_failure(delivery, endpoint, f"request error: {exc}")

        return delivery

    async def _handle_failure(
        self, delivery: WebhookDelivery, endpoint: WebhookEndpoint, error: str
    ) -> WebhookDelivery:
        delivery = delivery.model_copy(update={"error": error})

        if delivery.attempt < delivery.max_attempts:
            delivery = delivery.model_copy(
                update={
                    "status": DeliveryStatus.RETRYING,
                    "attempt": delivery.attempt + 1,
                }
            )
            self._deliveries[delivery.id] = delivery
            enqueued = await self._retry_queue.enqueue(delivery)
            self._deliveries[delivery.id] = enqueued
            self._events.append(
                WebhookRetrying(
                    delivery_id=delivery.id,
                    endpoint_id=endpoint.id,
                    event_type_name=delivery.event_type,
                    attempt=enqueued.attempt,
                    next_retry_at=enqueued.next_retry_at or utc_now(),
                )
            )
        else:
            delivery = delivery.model_copy(update={"status": DeliveryStatus.FAILED})
            self._deliveries[delivery.id] = delivery
            self._events.append(
                WebhookDeliveryFailed(
                    delivery_id=delivery.id,
                    endpoint_id=endpoint.id,
                    event_type_name=delivery.event_type,
                    error=error,
                    attempt=delivery.attempt,
                )
            )

        return delivery

    def _record_receipt(
        self,
        delivery: WebhookDelivery,
        headers_sent: dict[str, str],
        status_code: int,
        duration_ms: float,
    ) -> DeliveryReceipt:
        receipt = DeliveryReceipt(
            id=str(uuid.uuid4()),
            delivery_id=delivery.id,
            endpoint_id=delivery.endpoint_id,
            status=delivery.status,
            headers_sent=headers_sent,
            response_summary={
                "status_code": status_code,
                "duration_ms": duration_ms,
                "event_type": delivery.event_type,
            },
            checksum="",
        )
        self._receipts[receipt.id] = receipt
        return receipt

    # -- Retry and cancellation -----------------------------------------------

    async def retry_delivery(self, delivery_id: str) -> WebhookDelivery:
        delivery = self._deliveries.get(delivery_id)
        if delivery is None:
            raise DeliveryError(f"Delivery '{delivery_id}' not found")
        endpoint = self.get(delivery.endpoint_id)
        delivery = delivery.model_copy(update={"attempt": delivery.attempt + 1})
        self._deliveries[delivery.id] = delivery
        return await self._send(delivery, endpoint)

    async def cancel_delivery(self, delivery_id: str) -> WebhookDelivery:
        delivery = self._deliveries.get(delivery_id)
        if delivery is None:
            raise DeliveryError(f"Delivery '{delivery_id}' not found")
        delivery = delivery.model_copy(update={"status": DeliveryStatus.FAILED})
        self._deliveries[delivery_id] = delivery
        return delivery

    async def get_delivery(self, delivery_id: str) -> WebhookDelivery:
        delivery = self._deliveries.get(delivery_id)
        if delivery is None:
            raise DeliveryError(f"Delivery '{delivery_id}' not found")
        return delivery

    async def list_deliveries(
        self,
        endpoint_id: str | None = None,
        status: DeliveryStatus | None = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        results = list(self._deliveries.values())
        if endpoint_id is not None:
            results = [d for d in results if d.endpoint_id == endpoint_id]
        if status is not None:
            results = [d for d in results if d.status == status]
        results.sort(key=lambda d: d.last_attempt_at or d.delivered_at or utc_now(), reverse=True)
        return results[:limit]

    # -- Event drain ----------------------------------------------------------

    def drain_events(self) -> list[Any]:
        events = list(self._events)
        self._events.clear()
        return events


__all__ = ["WebhookDispatcher"]
