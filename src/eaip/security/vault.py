"""Secret vault — in-memory encrypted secret storage."""

from __future__ import annotations

import base64
from typing import Any

from eaip.logging.context import get_logger
from eaip.security.events import SecretAccessed, SecretExpired, SecretRotated, SecretStored
from eaip.security.exceptions import SecretNotFoundError
from eaip.security.models import Secret, SecretType
from eaip.shared.time import utc_now

logger = get_logger("eaip.security.vault")


class SecretVault:
    """In-memory vault that stores secrets with simulated encryption."""

    def __init__(self) -> None:
        self._secrets: dict[str, _EncryptedSecret] = {}
        self._event_log: list[Any] = []

    async def store_secret(self, secret: Secret) -> str:
        encoded = self._encode(secret.value)
        self._secrets[secret.id] = _EncryptedSecret(secret=secret, encrypted_value=encoded)
        self._event_log.append(
            SecretStored(
                secret_id=secret.id, secret_name=secret.name, secret_type=secret.type.value
            )
        )
        logger.info("secret_stored", secret_id=secret.id, name=secret.name)
        return secret.id

    async def get_secret(self, secret_id: str) -> Secret:
        entry = self._secrets.get(secret_id)
        if entry is None:
            raise SecretNotFoundError(f"Secret {secret_id} not found")
        self._event_log.append(SecretAccessed(secret_id=secret_id, secret_name=entry.secret.name))
        return entry.secret

    async def get_secret_value(self, secret_id: str) -> str:
        entry = self._secrets.get(secret_id)
        if entry is None:
            raise SecretNotFoundError(f"Secret {secret_id} not found")
        value = self._decode(entry.encrypted_value)
        self._event_log.append(SecretAccessed(secret_id=secret_id, secret_name=entry.secret.name))
        return value

    async def delete_secret(self, secret_id: str) -> None:
        if secret_id not in self._secrets:
            raise SecretNotFoundError(f"Secret {secret_id} not found")
        del self._secrets[secret_id]
        logger.info("secret_deleted", secret_id=secret_id)

    async def list_secrets(
        self, type: SecretType | None = None, tags: tuple[str, ...] | None = None
    ) -> list[Secret]:
        results: list[Secret] = []
        for entry in self._secrets.values():
            s = entry.secret
            if type is not None and s.type != type:
                continue
            if tags is not None and not all(t in s.tags for t in tags):
                continue
            results.append(s)
        return results

    async def rotate_secret(self, secret_id: str) -> Secret:
        entry = self._secrets.get(secret_id)
        if entry is None:
            raise SecretNotFoundError(f"Secret {secret_id} not found")
        old = entry.secret
        new_version = old.version + 1
        rotated = Secret(
            id=old.id,
            name=old.name,
            type=old.type,
            value=old.value,
            description=old.description,
            tags=old.tags,
            metadata={**old.metadata, "rotated_from_version": old.version},
            created_at=utc_now(),
            expires_at=old.expires_at,
            rotation_period_days=old.rotation_period_days,
            version=new_version,
            enabled=old.enabled,
        )
        self._secrets[secret_id] = _EncryptedSecret(
            secret=rotated, encrypted_value=self._encode(rotated.value)
        )
        self._event_log.append(
            SecretRotated(
                secret_id=secret_id,
                secret_name=rotated.name,
                new_version=new_version,
                previous_version=old.version,
            )
        )
        logger.info("secret_rotated", secret_id=secret_id, new_version=new_version)
        return rotated

    async def check_expiry(self) -> list[Secret]:
        now = utc_now()
        expired: list[Secret] = []
        for entry in list(self._secrets.values()):
            s = entry.secret
            if s.expires_at is not None and s.expires_at <= now:
                expired.append(s)
                self._event_log.append(
                    SecretExpired(secret_id=s.id, secret_name=s.name, expired_at=s.expires_at)
                )
                logger.warning("secret_expired", secret_id=s.id, name=s.name)
        return expired

    def _encode(self, value: str) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("ascii")

    def _decode(self, encoded: str) -> str:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")

    @property
    def event_log(self) -> list[Any]:
        return self._event_log


class _EncryptedSecret:
    """Internal representation wrapping a secret with its encrypted value."""

    __slots__ = ("encrypted_value", "secret")

    def __init__(self, secret: Secret, encrypted_value: str) -> None:
        self.secret = secret
        self.encrypted_value = encrypted_value
