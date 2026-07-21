"""HMAC-SHA256 signing and secret management for webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Any

from eaip.shared.time import utc_now
from eaip.webhooks.models import WebhookSecret


class SignatureService:
    """Manages HMAC-SHA256 signing and verification of webhook payloads."""

    def __init__(self) -> None:
        self._secrets: dict[str, WebhookSecret] = {}

    async def sign_payload(self, payload: dict[str, Any], secret: str) -> str:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    async def verify_signature(self, payload: dict[str, Any], signature: str, secret: str) -> bool:
        expected = await self.sign_payload(payload, secret)
        return hmac.compare_digest(expected, signature)

    async def rotate_secret(self, endpoint_id: str) -> WebhookSecret:
        old_secrets = [
            s for s in self._secrets.values() if s.endpoint_id == endpoint_id and s.active
        ]
        for s in old_secrets:
            self._secrets[s.id] = s.model_copy(update={"active": False})

        now = utc_now()
        new_secret = WebhookSecret(
            id=str(uuid.uuid4()),
            endpoint_id=endpoint_id,
            key=uuid.uuid4().hex,
            version=max(
                (s.version for s in self._secrets.values() if s.endpoint_id == endpoint_id),
                default=0,
            )
            + 1,
            created_at=now,
            expires_at=None,
            active=True,
        )
        self._secrets[new_secret.id] = new_secret
        return new_secret

    async def get_active_secret(self, endpoint_id: str) -> WebhookSecret | None:
        for s in self._secrets.values():
            if s.endpoint_id == endpoint_id and s.active:
                if s.expires_at is None or s.expires_at > utc_now():
                    return s
        return None

    async def list_secrets(self, endpoint_id: str) -> list[WebhookSecret]:
        return sorted(
            [s for s in self._secrets.values() if s.endpoint_id == endpoint_id],
            key=lambda s: s.version,
            reverse=True,
        )


__all__ = ["SignatureService"]
