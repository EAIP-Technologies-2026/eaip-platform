"""Tests for :mod:`eaip.security.crypto`."""

from __future__ import annotations

import pytest

from eaip.security.crypto import EncryptionService
from eaip.security.events import KeyGenerated, KeyRotated
from eaip.security.exceptions import DecryptionError, EncryptionError
from eaip.security.models import EncryptionAlgorithm


class TestEncryptionService:
    async def test_generate_key(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        assert key.algorithm is EncryptionAlgorithm.AES256
        assert key.key_size == 256
        assert key.enabled is True

    async def test_encrypt_decrypt(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        encrypted = await svc.encrypt("hello world", key.id)
        assert encrypted != "hello world"
        decrypted = await svc.decrypt(encrypted, key.id)
        assert decrypted == "hello world"

    async def test_decrypt_wrong_key(self) -> None:
        svc = EncryptionService()
        key1 = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        key2 = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        encrypted = await svc.encrypt("test", key1.id)
        with pytest.raises(DecryptionError):
            await svc.decrypt(encrypted, key2.id)

    async def test_encrypt_with_unknown_key(self) -> None:
        svc = EncryptionService()
        with pytest.raises(EncryptionError):
            await svc.encrypt("data", "unknown-key")

    async def test_decrypt_with_unknown_key(self) -> None:
        svc = EncryptionService()
        with pytest.raises(DecryptionError):
            await svc.decrypt("encrypted", "unknown-key")

    async def test_rotate_key(self) -> None:
        svc = EncryptionService()
        old_key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        original_id = old_key.id
        new_key = await svc.rotate_key(original_id)
        assert new_key.id != original_id
        old_meta = await svc.get_key(original_id)
        assert old_meta.enabled is False

    async def test_rotate_unknown_key(self) -> None:
        svc = EncryptionService()
        with pytest.raises(EncryptionError):
            await svc.rotate_key("unknown")

    async def test_list_keys(self) -> None:
        svc = EncryptionService()
        await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        await svc.generate_key(EncryptionAlgorithm.RSA2048, 2048)
        keys = await svc.list_keys()
        assert len(keys) == 2

    async def test_get_key(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.ECC, 256)
        retrieved = await svc.get_key(key.id)
        assert retrieved.id == key.id
        assert retrieved.name == key.name

    async def test_encrypt_empty_string(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        encrypted = await svc.encrypt("", key.id)
        decrypted = await svc.decrypt(encrypted, key.id)
        assert decrypted == ""

    async def test_encrypt_special_characters(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        data = "hello\nworld\t!@#$%^&*()"
        encrypted = await svc.encrypt(data, key.id)
        decrypted = await svc.decrypt(encrypted, key.id)
        assert decrypted == data

    async def test_generate_key_event(self) -> None:
        svc = EncryptionService()
        await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        assert any(isinstance(e, KeyGenerated) for e in svc.event_log)

    async def test_rotate_key_event(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        await svc.rotate_key(key.id)
        assert any(isinstance(e, KeyRotated) for e in svc.event_log)

    async def test_decrypt_disabled_key(self) -> None:
        svc = EncryptionService()
        key = await svc.generate_key(EncryptionAlgorithm.AES256, 256)
        encrypted = await svc.encrypt("test", key.id)
        await svc.rotate_key(key.id)
        with pytest.raises(DecryptionError):
            await svc.decrypt(encrypted, key.id)
