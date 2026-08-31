"""Encryption service — key management and data encryption."""

from __future__ import annotations

import base64
import uuid
from datetime import timedelta
from typing import Any

from cryptography.fernet import Fernet

from eaip.logging.context import get_logger
from eaip.security.events import KeyGenerated, KeyRotated
from eaip.security.exceptions import DecryptionError, EncryptionError
from eaip.security.models import EncryptionAlgorithm, EncryptionKey
from eaip.shared.time import utc_now

logger = get_logger("eaip.security.crypto")


class EncryptionService:
    """Fernet-based symmetric encryption with key lifecycle management."""

    def __init__(self) -> None:
        self._keys: dict[str, _KeyEntry] = {}
        self._event_log: list[Any] = []

    async def encrypt(self, data: str, key_id: str) -> str:
        entry = self._keys.get(key_id)
        if entry is None:
            raise EncryptionError(f"Key {key_id} not found")
        if not entry.key.enabled:
            raise EncryptionError(f"Key {key_id} is disabled")
        try:
            encrypted = entry.fernet.encrypt(data.encode("utf-8"))
            return base64.b64encode(encrypted).decode("ascii")
        except Exception as exc:
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    async def decrypt(self, encrypted_data: str, key_id: str) -> str:
        entry = self._keys.get(key_id)
        if entry is None:
            raise DecryptionError(f"Key {key_id} not found")
        if not entry.key.enabled:
            raise DecryptionError(f"Key {key_id} is disabled")
        try:
            raw = base64.b64decode(encrypted_data.encode("ascii"))
            decrypted = entry.fernet.decrypt(raw)
            return decrypted.decode("utf-8")
        except Exception as exc:
            raise DecryptionError(f"Decryption failed: {exc}") from exc

    async def generate_key(self, algorithm: EncryptionAlgorithm, key_size: int) -> EncryptionKey:
        key_id = str(uuid.uuid4())
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        now = utc_now()
        key = EncryptionKey(
            id=key_id,
            name=f"key-{algorithm.value}-{key_id[:8]}",
            algorithm=algorithm,
            key_size=key_size,
            created_at=now,
            rotation_due_at=now + timedelta(days=90),
        )
        self._keys[key_id] = _KeyEntry(key=key, fernet=fernet, raw=fernet_key.decode("ascii"))
        self._event_log.append(
            KeyGenerated(
                key_id=key_id, key_name=key.name, algorithm=algorithm.value, key_size=key_size
            )
        )
        logger.info("key_generated", key_id=key_id, algorithm=algorithm.value)
        return key

    async def rotate_key(self, key_id: str) -> EncryptionKey:
        entry = self._keys.get(key_id)
        if entry is None:
            raise EncryptionError(f"Key {key_id} not found")
        old_key = entry.key
        old_key_disabled = EncryptionKey(
            id=old_key.id,
            name=old_key.name,
            algorithm=old_key.algorithm,
            key_size=old_key.key_size,
            created_at=old_key.created_at,
            expires_at=old_key.expires_at,
            enabled=False,
            metadata={**old_key.metadata, "rotated_at": utc_now().isoformat()},
            rotation_due_at=old_key.rotation_due_at,
        )
        new_key_id = str(uuid.uuid4())
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        now = utc_now()
        new_key = EncryptionKey(
            id=new_key_id,
            name=old_key.name,
            algorithm=old_key.algorithm,
            key_size=old_key.key_size,
            created_at=now,
            rotation_due_at=now + timedelta(days=90),
        )
        self._keys[key_id] = _KeyEntry(key=old_key_disabled, fernet=entry.fernet, raw=entry.raw)
        self._keys[new_key_id] = _KeyEntry(
            key=new_key, fernet=fernet, raw=fernet_key.decode("ascii")
        )
        self._event_log.append(
            KeyRotated(key_id=key_id, key_name=old_key.name, new_key_id=new_key_id)
        )
        logger.info("key_rotated", old_key_id=key_id, new_key_id=new_key_id)
        return new_key

    async def get_key(self, key_id: str) -> EncryptionKey:
        entry = self._keys.get(key_id)
        if entry is None:
            raise EncryptionError(f"Key {key_id} not found")
        return entry.key

    async def list_keys(self) -> list[EncryptionKey]:
        return [entry.key for entry in self._keys.values()]

    @property
    def event_log(self) -> list[Any]:
        return self._event_log


class _KeyEntry:
    """Internal key storage wrapping metadata with a Fernet instance."""

    __slots__ = ("fernet", "key", "raw")

    def __init__(self, key: EncryptionKey, fernet: Fernet, raw: str) -> None:
        self.key = key
        self.fernet = fernet
        self.raw = raw
