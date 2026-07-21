"""Tests for the export delivery service."""

from __future__ import annotations

import pytest

from eaip.export.delivery import DeliveryService
from eaip.export.exceptions import DeliveryFailedError
from eaip.export.models import DeliveryConfig, ExportJob


class TestDeliverEmail:
    def test_deliver_email_success(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        config = DeliveryConfig(channels=("email",), email_recipients=("user@eaip.dev",))
        result = svc.deliver_email(job, config)
        assert "email" in result.delivery_status
        assert result.delivery_status["email"]["status"] == "delivered"

    def test_deliver_email_no_recipients_raises(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        config = DeliveryConfig(channels=("email",))
        with pytest.raises(DeliveryFailedError):
            svc.deliver_email(job, config)


class TestDeliverStorage:
    def test_deliver_storage_success(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1", output_path="/tmp/test_export_j1.txt")
        config = DeliveryConfig(channels=("storage",), storage_path="/tmp/test_export_j1.txt")
        result = svc.deliver_storage(job, config)
        assert "storage" in result.delivery_status
        assert result.delivery_status["storage"]["status"] == "delivered"

    def test_deliver_storage_no_path_raises(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        config = DeliveryConfig(channels=("storage",))
        with pytest.raises(DeliveryFailedError):
            svc.deliver_storage(job, config)


class TestDeliverWebhook:
    def test_deliver_webhook_no_url_raises(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        config = DeliveryConfig(channels=("webhook",))
        with pytest.raises(DeliveryFailedError):
            svc.deliver_webhook(job, config)


class TestDeliverExport:
    def test_deliver_export_storage_channel(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1", output_path="/tmp/test_export_j1_deliver.txt")
        config = DeliveryConfig(
            channels=("storage",), storage_path="/tmp/test_export_j1_deliver.txt"
        )
        result = svc.deliver_export(job, config)
        assert "storage" in result.delivery_status

    def test_deliver_export_email_channel(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        config = DeliveryConfig(channels=("email",), email_recipients=("admin@eaip.dev",))
        result = svc.deliver_export(job, config)
        assert "email" in result.delivery_status

    def test_deliver_export_multiple_channels(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1", output_path="/tmp/test_export_j1_multi.txt")
        config = DeliveryConfig(
            channels=("storage", "email"),
            email_recipients=("admin@eaip.dev",),
            storage_path="/tmp/test_export_j1_multi.txt",
        )
        result = svc.deliver_export(job, config)
        assert "storage" in result.delivery_status
        assert "email" in result.delivery_status


class TestUpdateDeliveryStatus:
    def test_update_status(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        result = svc.update_delivery_status(job, "email", "sent", "Delivered OK")
        assert result.delivery_status["email"]["status"] == "sent"
        assert result.delivery_status["email"]["details"] == "Delivered OK"

    def test_update_multiple_channels(self) -> None:
        svc = DeliveryService()
        job = ExportJob(id="j1", report_id="r1")
        result = svc.update_delivery_status(job, "email", "sent")
        result = svc.update_delivery_status(result, "storage", "delivered")
        assert result.delivery_status["email"]["status"] == "sent"
        assert result.delivery_status["storage"]["status"] == "delivered"


class TestEventHandlers:
    def test_event_handler_invoked_on_deliver(self) -> None:
        svc = DeliveryService()
        events: list[str] = []

        class Handler:
            def on_ExportDelivered(self, event: object) -> None:
                events.append("delivered")

        svc.register_event_handler(Handler())
        job = ExportJob(id="j1", report_id="r1", output_path="/tmp/test_export_j1_event.txt")
        config = DeliveryConfig(channels=("storage",), storage_path="/tmp/test_export_j1_event.txt")
        svc.deliver_storage(job, config)
        assert "delivered" in events
