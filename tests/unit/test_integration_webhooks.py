"""Tests for WebhookManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eaip.integration.exceptions import WebhookDeliveryError
from eaip.integration.models import WebhookRegistration
from eaip.integration.webhooks import WebhookManager


class TestWebhookManagerRegistration:
    def test_register_webhook(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        mgr.register_webhook(w)
        assert mgr.get_webhook("w1") is not None
        assert mgr.get_webhook("w1").id == "w1"

    def test_unregister_webhook(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        mgr.register_webhook(w)
        removed = mgr.unregister_webhook("w1")
        assert removed is not None
        assert mgr.get_webhook("w1") is None

    def test_unregister_missing(self) -> None:
        mgr = WebhookManager()
        assert mgr.unregister_webhook("nonexistent") is None

    def test_get_webhook_missing(self) -> None:
        mgr = WebhookManager()
        assert mgr.get_webhook("nonexistent") is None


class TestWebhookManagerTrigger:
    @pytest.mark.asyncio
    async def test_trigger_missing_webhook(self) -> None:
        mgr = WebhookManager()
        with pytest.raises(WebhookDeliveryError):
            await mgr.trigger_webhook("nonexistent", {"key": "value"})

    @pytest.mark.asyncio
    async def test_trigger_disabled_webhook(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(
            id="w1", name="Hook1", url="https://hooks.example.com", enabled=False
        )
        mgr.register_webhook(w)
        with pytest.raises(WebhookDeliveryError):
            await mgr.trigger_webhook("w1", {"key": "value"})

    @pytest.mark.asyncio
    async def test_trigger_event_bus(self) -> None:
        mock_bus = AsyncMock()
        mgr = WebhookManager(event_bus=mock_bus)
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        mgr.register_webhook(w)
        with patch.object(
            mgr, "deliver_webhook", AsyncMock(return_value={"status_code": 200, "duration_ms": 10})
        ):
            result = await mgr.trigger_webhook("w1", {"key": "value"})
            assert result["status_code"] == 200


class TestWebhookManagerDeliver:
    @pytest.mark.asyncio
    async def test_deliver_success(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await mgr.deliver_webhook(w, {"key": "value"})
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_deliver_with_secret(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(
            id="w1", name="Hook1", url="https://hooks.example.com", secret="s3cret"
        )
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await mgr.deliver_webhook(w, {"key": "value"})
            call_kwargs = mock_post.call_args[1]
            assert "X-Webhook-Signature" in call_kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_deliver_network_error(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            with pytest.raises(WebhookDeliveryError):
                await mgr.deliver_webhook(w, {"key": "value"})

    @pytest.mark.asyncio
    async def test_deliver_event_bus(self) -> None:
        mock_bus = AsyncMock()
        mgr = WebhookManager(event_bus=mock_bus)
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com")
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            await mgr.deliver_webhook(w, {"key": "value"})
            mock_bus.publish.assert_called()


class TestWebhookManagerVerify:
    @pytest.mark.asyncio
    async def test_verify_signature_valid(self) -> None:
        mgr = WebhookManager()
        payload = '{"key": "value"}'
        secret = "s3cret"
        import hashlib
        import hmac

        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert await mgr.verify_signature(payload, expected, secret) is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid(self) -> None:
        mgr = WebhookManager()
        assert await mgr.verify_signature('{"key": "value"}', "invalid_sig", "secret") is False

    @pytest.mark.asyncio
    async def test_verify_signature_empty_secret(self) -> None:
        mgr = WebhookManager()
        payload = '{"key": "value"}'
        import hashlib
        import hmac

        expected = hmac.new(b"", payload.encode(), hashlib.sha256).hexdigest()
        assert await mgr.verify_signature(payload, expected, "") is True


class TestWebhookManagerProcessIncoming:
    @pytest.mark.asyncio
    async def test_process_incoming_matches_url(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com/event")
        mgr.register_webhook(w)
        matched = await mgr.process_incoming_webhook(
            "https://hooks.example.com/event", {}, {"key": "value"}
        )
        assert len(matched) == 1

    @pytest.mark.asyncio
    async def test_process_incoming_no_match(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com/event")
        mgr.register_webhook(w)
        matched = await mgr.process_incoming_webhook("https://other.com/hook", {}, {"key": "value"})
        assert len(matched) == 0

    @pytest.mark.asyncio
    async def test_process_incoming_disabled(self) -> None:
        mgr = WebhookManager()
        w = WebhookRegistration(
            id="w1", name="Hook1", url="https://hooks.example.com/event", enabled=False
        )
        mgr.register_webhook(w)
        matched = await mgr.process_incoming_webhook(
            "https://hooks.example.com/event", {}, {"key": "value"}
        )
        assert len(matched) == 0

    @pytest.mark.asyncio
    async def test_process_incoming_event_bus(self) -> None:
        mock_bus = AsyncMock()
        mgr = WebhookManager(event_bus=mock_bus)
        w = WebhookRegistration(id="w1", name="Hook1", url="https://hooks.example.com/event")
        mgr.register_webhook(w)
        await mgr.process_incoming_webhook("https://hooks.example.com/event", {}, {"key": "value"})
        mock_bus.publish.assert_called()
