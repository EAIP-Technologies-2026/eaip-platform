"""Tests for :mod:`eaip.security.vault`."""

from __future__ import annotations

import pytest

from eaip.security.events import SecretAccessed, SecretRotated, SecretStored
from eaip.security.exceptions import SecretNotFoundError
from eaip.security.models import Secret, SecretType
from eaip.security.vault import SecretVault


class TestSecretVault:
    async def test_store_and_retrieve_secret(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.API_KEY, value="my-api-key")
        stored_id = await vault.store_secret(s)
        retrieved = await vault.get_secret("s1")
        assert stored_id == "s1"
        assert retrieved.id == "s1"
        assert retrieved.name == "test"

    async def test_get_secret_not_found(self) -> None:
        vault = SecretVault()
        with pytest.raises(SecretNotFoundError):
            await vault.get_secret("nonexistent")

    async def test_get_secret_value(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="key", type=SecretType.TOKEN, value="super-secret-value")
        await vault.store_secret(s)
        value = await vault.get_secret_value("s1")
        assert value == "super-secret-value"

    async def test_get_secret_value_not_found(self) -> None:
        vault = SecretVault()
        with pytest.raises(SecretNotFoundError):
            await vault.get_secret_value("nonexistent")

    async def test_delete_secret(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.PASSWORD, value="pass")
        await vault.store_secret(s)
        await vault.delete_secret("s1")
        with pytest.raises(SecretNotFoundError):
            await vault.get_secret("s1")

    async def test_delete_secret_not_found(self) -> None:
        vault = SecretVault()
        with pytest.raises(SecretNotFoundError):
            await vault.delete_secret("nonexistent")

    async def test_list_secrets_all(self) -> None:
        vault = SecretVault()
        await vault.store_secret(Secret(id="s1", name="a", type=SecretType.API_KEY, value="v1"))
        await vault.store_secret(Secret(id="s2", name="b", type=SecretType.PASSWORD, value="v2"))
        secrets = await vault.list_secrets()
        assert len(secrets) == 2

    async def test_list_secrets_filter_by_type(self) -> None:
        vault = SecretVault()
        await vault.store_secret(Secret(id="s1", name="a", type=SecretType.API_KEY, value="v1"))
        await vault.store_secret(Secret(id="s2", name="b", type=SecretType.PASSWORD, value="v2"))
        secrets = await vault.list_secrets(type=SecretType.API_KEY)
        assert len(secrets) == 1
        assert secrets[0].id == "s1"

    async def test_list_secrets_filter_by_tags(self) -> None:
        vault = SecretVault()
        await vault.store_secret(
            Secret(id="s1", name="a", type=SecretType.API_KEY, value="v1", tags=("prod",))
        )
        await vault.store_secret(
            Secret(id="s2", name="b", type=SecretType.TOKEN, value="v2", tags=("dev",))
        )
        secrets = await vault.list_secrets(tags=("prod",))
        assert len(secrets) == 1
        assert secrets[0].id == "s1"

    async def test_list_secrets_filter_by_type_and_tags(self) -> None:
        vault = SecretVault()
        await vault.store_secret(
            Secret(id="s1", name="a", type=SecretType.API_KEY, value="v1", tags=("prod", "db"))
        )
        await vault.store_secret(
            Secret(id="s2", name="b", type=SecretType.API_KEY, value="v2", tags=("dev",))
        )
        await vault.store_secret(
            Secret(id="s3", name="c", type=SecretType.PASSWORD, value="v3", tags=("prod",))
        )
        secrets = await vault.list_secrets(type=SecretType.API_KEY, tags=("prod",))
        assert len(secrets) == 1
        assert secrets[0].id == "s1"

    async def test_rotate_secret(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.CREDENTIAL, value="original", version=1)
        await vault.store_secret(s)
        rotated = await vault.rotate_secret("s1")
        assert rotated.version == 2
        assert rotated.metadata["rotated_from_version"] == 1

    async def test_rotate_secret_not_found(self) -> None:
        vault = SecretVault()
        with pytest.raises(SecretNotFoundError):
            await vault.rotate_secret("nonexistent")

    async def test_rotate_preserves_decrypted_value(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.API_KEY, value="my-secret-value")
        await vault.store_secret(s)
        await vault.rotate_secret("s1")
        value = await vault.get_secret_value("s1")
        assert value == "my-secret-value"

    async def test_check_expiry_no_expired(self) -> None:
        vault = SecretVault()
        await vault.store_secret(Secret(id="s1", name="a", type=SecretType.TOKEN, value="v1"))
        expired = await vault.check_expiry()
        assert expired == []

    async def test_store_secret_event_emitted(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.API_KEY, value="v")
        await vault.store_secret(s)
        assert any(isinstance(e, SecretStored) and e.secret_id == "s1" for e in vault.event_log)

    async def test_access_secret_event_emitted(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.API_KEY, value="v")
        await vault.store_secret(s)
        await vault.get_secret("s1")
        assert any(isinstance(e, SecretAccessed) and e.secret_id == "s1" for e in vault.event_log)

    async def test_rotate_secret_event_emitted(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.API_KEY, value="v")
        await vault.store_secret(s)
        await vault.rotate_secret("s1")
        assert any(isinstance(e, SecretRotated) and e.secret_id == "s1" for e in vault.event_log)

    async def test_multiple_secrets_isolated(self) -> None:
        vault = SecretVault()
        await vault.store_secret(Secret(id="s1", name="a", type=SecretType.API_KEY, value="v1"))
        await vault.store_secret(Secret(id="s2", name="b", type=SecretType.PASSWORD, value="v2"))
        assert await vault.get_secret_value("s1") == "v1"
        assert await vault.get_secret_value("s2") == "v2"

    async def test_secret_encodes_value(self) -> None:
        vault = SecretVault()
        s = Secret(id="s1", name="test", type=SecretType.TOKEN, value="raw-value")
        await vault.store_secret(s)
        stored = vault._secrets["s1"]
        assert stored.encrypted_value != "raw-value"
        decoded = vault._decode(stored.encrypted_value)
        assert decoded == "raw-value"
