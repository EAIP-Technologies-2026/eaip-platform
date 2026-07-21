"""Tests for :mod:`eaip.dataencrypt.encryptor`."""

from __future__ import annotations

import pytest

from eaip.dataencrypt.encryptor import DataEncryptionService
from eaip.dataencrypt.models import EncryptionAlgorithm, EncryptionKey, EncryptionRequest


class TestDataEncryptionService:
    @pytest.fixture
    def service(self) -> DataEncryptionService:
        return DataEncryptionService()

    @pytest.fixture
    def aes_key(self) -> EncryptionKey:
        return EncryptionKey(id="k1", name="aes-master", algorithm=EncryptionAlgorithm.AES256)

    async def test_create_and_get_key(self, service: DataEncryptionService) -> None:
        key = EncryptionKey(id="k1", name="test-key", algorithm=EncryptionAlgorithm.AES256)
        created = await service.create_key(key)
        assert created.id == "k1"
        fetched = await service.get_key("k1")
        assert fetched.name == "test-key"

    async def test_get_key_not_found(self, service: DataEncryptionService) -> None:
        with pytest.raises(Exception):
            await service.get_key("nonexistent")

    async def test_deactivate_key(
        self, service: DataEncryptionService, aes_key: EncryptionKey
    ) -> None:
        await service.create_key(aes_key)
        deactivated = await service.deactivate_key("k1")
        assert deactivated.status.value == "deactivated"

    async def test_list_keys(self, service: DataEncryptionService) -> None:
        k1 = EncryptionKey(id="k1", name="k1", algorithm=EncryptionAlgorithm.AES256)
        k2 = EncryptionKey(id="k2", name="k2", algorithm=EncryptionAlgorithm.RSA4096)
        await service.create_key(k1)
        await service.create_key(k2)
        keys = await service.list_keys()
        assert len(keys) == 2

    async def test_rotate_key(self, service: DataEncryptionService, aes_key: EncryptionKey) -> None:
        await service.create_key(aes_key)
        rotated = await service.rotate_key("k1", EncryptionAlgorithm.RSA4096)
        assert rotated.algorithm is EncryptionAlgorithm.RSA4096
        assert rotated.id != "k1"

    async def test_encrypt(self, service: DataEncryptionService, aes_key: EncryptionKey) -> None:
        await service.create_key(aes_key)
        req = EncryptionRequest(
            id="req1",
            payload_ref="blob://secret",
            algorithm=EncryptionAlgorithm.AES256,
            key_id="k1",
        )
        result = await service.encrypt(req)
        assert result.encrypted_ref.startswith("enc://")
        assert result.key_id == "k1"

    async def test_decrypt(self, service: DataEncryptionService, aes_key: EncryptionKey) -> None:
        await service.create_key(aes_key)
        result = await service.decrypt("blob://secret", "k1")
        assert result.encrypted_ref.startswith("dec://")
