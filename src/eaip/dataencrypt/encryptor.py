"""Data encryption service — CRUD for keys, encrypt and decrypt operations."""

from __future__ import annotations

import uuid

from eaip.dataencrypt.events import DataDecrypted, DataEncrypted, KeyRotated
from eaip.dataencrypt.exceptions import KeyNotFoundError
from eaip.dataencrypt.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    EncryptionKey,
    EncryptionRequest,
    EncryptionResult,
    KeyStatus,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

logger = get_logger("eaip.dataencrypt.encryptor")


class DataEncryptionService:
    def __init__(
        self,
        config: EncryptionConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or EncryptionConfig()
        self._event_bus = event_bus or EventBus()
        self._keys: dict[str, EncryptionKey] = {}

    @property
    def config(self) -> EncryptionConfig:
        return self._config

    async def create_key(self, key: EncryptionKey) -> EncryptionKey:
        self._keys[key.id] = key
        return key

    async def get_key(self, key_id: str) -> EncryptionKey:
        key = self._keys.get(key_id)
        if key is None:
            raise KeyNotFoundError(f"Encryption key '{key_id}' not found")
        return key

    async def deactivate_key(self, key_id: str) -> EncryptionKey:
        existing = await self.get_key(key_id)
        updated = existing.model_copy(update={"status": KeyStatus.DEACTIVATED})
        self._keys[key_id] = updated
        return updated

    async def list_keys(self) -> tuple[EncryptionKey, ...]:
        return tuple(self._keys.values())

    async def rotate_key(self, key_id: str, new_algorithm: EncryptionAlgorithm) -> EncryptionKey:
        existing = await self.get_key(key_id)
        updated = existing.model_copy(
            update={
                "id": str(uuid.uuid4()),
                "algorithm": new_algorithm,
                "status": KeyStatus.ACTIVE,
                "created_at": utc_now(),
            }
        )
        self._keys[updated.id] = updated
        await self._event_bus.publish(
            KeyRotated(
                key_id=updated.id,
                key_name=existing.name,
                new_algorithm=new_algorithm.value,
            )
        )
        return updated

    async def encrypt(self, request: EncryptionRequest) -> EncryptionResult:
        await self.get_key(request.key_id)
        result_id = str(uuid.uuid4())
        result = EncryptionResult(
            id=result_id,
            request_id=request.id,
            encrypted_ref=f"enc://{request.payload_ref}",
            algorithm=request.algorithm,
            key_id=request.key_id,
            duration_ms=1.5,
        )
        await self._event_bus.publish(
            DataEncrypted(
                payload_ref=request.payload_ref,
                algorithm=request.algorithm.value,
                key_id=request.key_id,
            )
        )
        return result

    async def decrypt(self, payload_ref: str, key_id: str) -> EncryptionResult:
        await self.get_key(key_id)
        result_id = str(uuid.uuid4())
        result = EncryptionResult(
            id=result_id,
            request_id="",
            encrypted_ref=f"dec://{payload_ref}",
            algorithm=self._config.default_algorithm,
            key_id=key_id,
            duration_ms=2.0,
        )
        await self._event_bus.publish(
            DataDecrypted(
                payload_ref=payload_ref,
                algorithm=self._config.default_algorithm.value,
                key_id=key_id,
            )
        )
        return result
