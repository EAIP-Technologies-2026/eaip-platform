"""Tests for webhook HMAC signing and secret management."""

from __future__ import annotations

import pytest

from eaip.webhooks.signing import SignatureService


class TestSignatureService:
    @pytest.mark.asyncio
    async def test_sign_and_verify(self) -> None:
        svc = SignatureService()
        payload = {"event": "order.created", "id": "123"}
        signature = await svc.sign_payload(payload, "my-secret")
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest
        assert await svc.verify_signature(payload, signature, "my-secret") is True

    @pytest.mark.asyncio
    async def test_wrong_secret_fails_verification(self) -> None:
        svc = SignatureService()
        payload = {"event": "order.created"}
        signature = await svc.sign_payload(payload, "correct-secret")
        assert await svc.verify_signature(payload, signature, "wrong-secret") is False

    @pytest.mark.asyncio
    async def test_different_payload_fails_verification(self) -> None:
        svc = SignatureService()
        sig1 = await svc.sign_payload({"a": 1}, "secret")
        sig2 = await svc.sign_payload({"a": 2}, "secret")
        assert sig1 != sig2

    @pytest.mark.asyncio
    async def test_signature_deterministic(self) -> None:
        svc = SignatureService()
        payload = {"event": "test", "data": {"nested": True}}
        sig1 = await svc.sign_payload(payload, "secret")
        sig2 = await svc.sign_payload(payload, "secret")
        assert sig1 == sig2

    @pytest.mark.asyncio
    async def test_rotate_secret_creates_new_active(self) -> None:
        svc = SignatureService()
        secret = await svc.rotate_secret("ep1")
        assert secret.endpoint_id == "ep1"
        assert secret.active is True
        assert secret.version == 1
        assert secret.key is not None

    @pytest.mark.asyncio
    async def test_rotate_secret_deactivates_old(self) -> None:
        svc = SignatureService()
        old = await svc.rotate_secret("ep1")
        old_id = old.id
        new = await svc.rotate_secret("ep1")
        secrets = await svc.list_secrets("ep1")
        old_stored = next(s for s in secrets if s.id == old_id)
        assert old_stored.active is False
        assert new.active is True
        assert new.version == 2

    @pytest.mark.asyncio
    async def test_get_active_secret(self) -> None:
        svc = SignatureService()
        assert await svc.get_active_secret("ep1") is None
        created = await svc.rotate_secret("ep1")
        active = await svc.get_active_secret("ep1")
        assert active is not None
        assert active.id == created.id

    @pytest.mark.asyncio
    async def test_list_secrets_ordered(self) -> None:
        svc = SignatureService()
        await svc.rotate_secret("ep1")
        await svc.rotate_secret("ep1")
        secrets = await svc.list_secrets("ep1")
        assert len(secrets) == 2
        assert secrets[0].version == 2
        assert secrets[1].version == 1

    @pytest.mark.asyncio
    async def test_empty_payload_signing(self) -> None:
        svc = SignatureService()
        sig = await svc.sign_payload({}, "secret")
        assert isinstance(sig, str)
        assert await svc.verify_signature({}, sig, "secret") is True
