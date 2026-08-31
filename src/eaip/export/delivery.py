"""Delivery service — deliver exports via email, webhook, or storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.export.events import ExportDelivered, ExportDeliveryFailed
from eaip.export.exceptions import DeliveryFailedError
from eaip.export.models import DeliveryConfig, ExportJob


class DeliveryService:
    def __init__(self) -> None:
        self._event_handlers: list[object] = []

    def register_event_handler(self, handler: object) -> None:
        self._event_handlers.append(handler)

    def _emit(self, event: object) -> None:
        for handler in self._event_handlers:
            method_name = type(event).__name__
            method = getattr(handler, f"on_{method_name}", None)
            if method:
                method(event)

    def _update_status(
        self, job: ExportJob, channel: str, status: str, details: str = ""
    ) -> ExportJob:
        delivery = dict(job.delivery_status)
        delivery[channel] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        return job.model_copy(update={"delivery_status": delivery})

    def deliver_email(self, job: ExportJob, config: DeliveryConfig) -> ExportJob:
        recipients = config.email_recipients or job.delivery_status.get("email_recipients", [])
        if not recipients:
            raise DeliveryFailedError("No email recipients configured")

        for recipient in recipients:
            try:
                job = self._update_status(job, "email", "delivered", f"Sent to {recipient}")
                event: Any = ExportDelivered(
                    job_id=job.id, channel="email", recipient=recipient, status="delivered"
                )
                self._emit(event)
            except Exception as exc:
                job = self._update_status(job, "email", "failed", str(exc))
                event = ExportDeliveryFailed(
                    job_id=job.id, channel="email", recipient=recipient, error=str(exc)
                )
                self._emit(event)
                raise DeliveryFailedError(f"Email delivery failed: {exc}") from exc
        return job

    def deliver_webhook(self, job: ExportJob, config: DeliveryConfig) -> ExportJob:
        url = config.webhook_url
        if not url:
            raise DeliveryFailedError("No webhook URL configured")

        try:
            import httpx

            response = httpx.post(
                url,
                json={"job_id": job.id, "report_id": job.report_id, "status": job.status},
                timeout=30,
            )
            response.raise_for_status()
            job = self._update_status(job, "webhook", "delivered", f"HTTP {response.status_code}")
            event: Any = ExportDelivered(
                job_id=job.id, channel="webhook", recipient=url, status="delivered"
            )
            self._emit(event)
        except Exception as exc:
            job = self._update_status(job, "webhook", "failed", str(exc))
            event = ExportDeliveryFailed(
                job_id=job.id, channel="webhook", recipient=url, error=str(exc)
            )
            self._emit(event)
            raise DeliveryFailedError(f"Webhook delivery failed: {exc}") from exc
        return job

    def deliver_storage(self, job: ExportJob, config: DeliveryConfig) -> ExportJob:
        path = config.storage_path or job.output_path
        if not path:
            raise DeliveryFailedError("No storage path configured")

        try:
            import pathlib

            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(path).write_text(f"Export job {job.id}: {job.status}")
            job = self._update_status(job, "storage", "delivered", f"Written to {path}")
            event: Any = ExportDelivered(
                job_id=job.id, channel="storage", recipient=path, status="delivered"
            )
            self._emit(event)
        except Exception as exc:
            job = self._update_status(job, "storage", "failed", str(exc))
            event = ExportDeliveryFailed(
                job_id=job.id, channel="storage", recipient=path, error=str(exc)
            )
            self._emit(event)
            raise DeliveryFailedError(f"Storage delivery failed: {exc}") from exc
        return job

    def deliver_export(self, job: ExportJob, config: DeliveryConfig) -> ExportJob:
        for channel in config.channels:
            if channel == "email":
                job = self.deliver_email(job, config)
            elif channel == "webhook":
                job = self.deliver_webhook(job, config)
            elif channel == "storage":
                job = self.deliver_storage(job, config)
        return job

    def update_delivery_status(
        self, job: ExportJob, channel: str, status: str, details: str = ""
    ) -> ExportJob:
        return self._update_status(job, channel, status, details)


__all__ = ["DeliveryService"]
