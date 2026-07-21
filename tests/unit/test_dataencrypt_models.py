"""Tests for :mod:`eaip.dataencrypt.models`."""

from __future__ import annotations

import pytest

from eaip.dataencrypt.models import (
    EncryptionAlgorithm,
    EncryptionConfig,
    EncryptionKey,
    EncryptionRequest,
    EncryptionResult,
    KeyStatus,
)


class TestEncryptionKey:
    def test_defaults(self) -> None:
        k = EncryptionKey(id="k1", name="master-key", algorithm=EncryptionAlgorithm.AES256)
        assert k.id == "k1"
        assert k.key_length == 256
        assert k.status is KeyStatus.ACTIVE

    def test_with_all_fields(self) -> None:
        from datetime import datetime

        k = EncryptionKey(
            id="k2",
            name="rsa-key",
            algorithm=EncryptionAlgorithm.RSA4096,
            key_length=4096,
            status=KeyStatus.ACTIVE,
            created_at=datetime(2025, 1, 1),
        )
        assert k.algorithm is EncryptionAlgorithm.RSA4096
        assert k.key_length == 4096

    def test_frozen(self) -> None:
        k = EncryptionKey(id="k1", name="n", algorithm=EncryptionAlgorithm.AES256)
        with pytest.raises((ValueError, TypeError)):
            k.name = "new"  # type: ignore[misc]

    def test_enum_values(self) -> None:
        assert EncryptionAlgorithm.AES256.value == "aes256"
        assert EncryptionAlgorithm.RSA4096.value == "rsa4096"
        assert KeyStatus.ACTIVE.value == "active"
        assert KeyStatus.DEACTIVATED.value == "deactivated"
        assert KeyStatus.COMPROMISED.value == "compromised"


class TestEncryptionRequest:
    def test_defaults(self) -> None:
        r = EncryptionRequest(
            id="req1", payload_ref="blob://data", algorithm=EncryptionAlgorithm.AES256, key_id="k1"
        )
        assert r.mode == "CBC"
        assert r.key_id == "k1"

    def test_frozen(self) -> None:
        r = EncryptionRequest(
            id="r1", payload_ref="p", algorithm=EncryptionAlgorithm.AES256, key_id="k"
        )
        with pytest.raises((ValueError, TypeError)):
            r.payload_ref = "new"  # type: ignore[misc]


class TestEncryptionResult:
    def test_defaults(self) -> None:
        r = EncryptionResult(
            id="res1",
            request_id="req1",
            algorithm=EncryptionAlgorithm.AES256,
            key_id="k1",
        )
        assert r.encrypted_ref == ""
        assert r.duration_ms == 0.0

    def test_frozen(self) -> None:
        r = EncryptionResult(
            id="r1", request_id="r", algorithm=EncryptionAlgorithm.AES256, key_id="k"
        )
        with pytest.raises((ValueError, TypeError)):
            r.algorithm = EncryptionAlgorithm.RSA4096  # type: ignore[misc]


class TestEncryptionConfig:
    def test_defaults(self) -> None:
        c = EncryptionConfig()
        assert c.default_algorithm is EncryptionAlgorithm.AES256
        assert c.key_rotation_days == 90
        assert c.max_encryption_retries == 3

    def test_custom_values(self) -> None:
        c = EncryptionConfig(
            default_algorithm=EncryptionAlgorithm.RSA4096,
            key_rotation_days=180,
            max_encryption_retries=5,
        )
        assert c.default_algorithm is EncryptionAlgorithm.RSA4096
        assert c.key_rotation_days == 180

    def test_frozen(self) -> None:
        c = EncryptionConfig()
        with pytest.raises((ValueError, TypeError)):
            c.key_rotation_days = 10  # type: ignore[misc]
