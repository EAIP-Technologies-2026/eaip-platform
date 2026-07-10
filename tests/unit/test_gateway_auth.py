"""Tests for :mod:`eaip.gateway.auth`."""

from __future__ import annotations

import pytest

from eaip.gateway.auth import ApiKeyStore
from eaip.gateway.exceptions import AuthError
from eaip.gateway.models import ApiKeyCredentials


class TestApiKeyStore:
    def test_register_and_validate(self) -> None:
        store = ApiKeyStore()
        creds = ApiKeyCredentials(key_id="k1", name="Test Key")
        raw = store.register_key(creds)
        assert isinstance(raw, str) and len(raw) > 0

        result = store.validate_key("k1", raw)
        assert result.key_id == "k1"
        assert result.name == "Test Key"

    def test_generated_key_is_unique(self) -> None:
        store = ApiKeyStore()
        k1 = store.register_key(ApiKeyCredentials(key_id="a", name="A"))
        k2 = store.register_key(ApiKeyCredentials(key_id="b", name="B"))
        assert k1 != k2

    def test_validate_invalid_key_id(self) -> None:
        store = ApiKeyStore()
        with pytest.raises(AuthError, match="Invalid API key"):
            store.validate_key("nonexistent", "some-key")

    def test_validate_wrong_key(self) -> None:
        store = ApiKeyStore()
        store.register_key(ApiKeyCredentials(key_id="k1", name="Test"), raw_key="correct")
        with pytest.raises(AuthError, match="Invalid API key"):
            store.validate_key("k1", "wrong")

    def test_disabled_key_rejected(self) -> None:
        store = ApiKeyStore()
        store.register_key(
            ApiKeyCredentials(key_id="k1", name="Disabled", enabled=False),
            raw_key="secret",
        )
        with pytest.raises(AuthError, match="disabled"):
            store.validate_key("k1", "secret")

    def test_revoke_key(self) -> None:
        store = ApiKeyStore()
        store.register_key(ApiKeyCredentials(key_id="k1", name="Test"), raw_key="secret")
        store.revoke_key("k1")
        with pytest.raises(AuthError):
            store.validate_key("k1", "secret")
        assert len(store.list_keys()) == 0

    def test_list_keys_excludes_secrets(self) -> None:
        store = ApiKeyStore()
        store.register_key(ApiKeyCredentials(key_id="k1", name="Alpha"), raw_key="s1")
        store.register_key(ApiKeyCredentials(key_id="k2", name="Beta"), raw_key="s2")
        keys = store.list_keys()
        assert len(keys) == 2
        names = {k.name for k in keys}
        assert names == {"Alpha", "Beta"}

    def test_list_keys_empty(self) -> None:
        store = ApiKeyStore()
        assert store.list_keys() == []
