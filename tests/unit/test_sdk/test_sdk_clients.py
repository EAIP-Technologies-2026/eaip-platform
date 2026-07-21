"""Tests for :mod:`eaip.sdk.clients`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.sdk.clients import ClientManager
from eaip.sdk.exceptions import ClientExpiredError, ClientNotFoundError
from eaip.sdk.models import ClientStatus


class TestClientManager:
    def test_create_client(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        assert client.id.startswith("cli-")
        assert client.sdk_id == "sdk-1"
        assert client.status is ClientStatus.ACTIVE
        assert client.api_key_id.startswith("ak-")

    def test_get_client(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        retrieved = mgr.get_client(client.id)
        assert retrieved.id == client.id
        assert retrieved.name == "MyApp"

    def test_get_client_not_found(self) -> None:
        mgr = ClientManager()
        with pytest.raises(ClientNotFoundError):
            mgr.get_client("nonexistent")

    def test_revoke_client(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        revoked = mgr.revoke_client(client.id)
        assert revoked.status is ClientStatus.REVOKED

    def test_revoke_nonexistent_client(self) -> None:
        mgr = ClientManager()
        with pytest.raises(ClientNotFoundError):
            mgr.revoke_client("nonexistent")

    def test_validate_client_valid(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        assert mgr.validate_client(client.id, client.api_key_id) is True

    def test_validate_client_wrong_key(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        assert mgr.validate_client(client.id, "wrong-key") is False

    def test_validate_client_revoked(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        mgr.revoke_client(client.id)
        assert mgr.validate_client(client.id, client.api_key_id) is False

    def test_validate_client_not_found(self) -> None:
        mgr = ClientManager()
        assert mgr.validate_client("nonexistent", "key") is False

    def test_validate_client_expired_by_date(self) -> None:
        mgr = ClientManager()
        past = datetime.now(UTC) - timedelta(days=1)
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp", expires_at=past)
        assert mgr.validate_client(client.id, client.api_key_id) is False

    def test_list_clients(self) -> None:
        mgr = ClientManager()
        mgr.create_client(sdk_id="sdk-1", name="App1")
        mgr.create_client(sdk_id="sdk-1", name="App2")
        mgr.create_client(sdk_id="sdk-2", name="App3")
        clients = mgr.list_clients("sdk-1")
        assert len(clients) == 2

    def test_update_client(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        updated = mgr.update_client(client.id, config={"env": "prod"})
        assert updated.configuration == {"env": "prod"}

    def test_update_client_not_found(self) -> None:
        mgr = ClientManager()
        with pytest.raises(ClientNotFoundError):
            mgr.update_client("nonexistent", config={})

    def test_record_client_usage(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        mgr.record_client_usage(client.id)
        updated = mgr.get_client(client.id)
        assert updated.last_used_at is not None

    def test_record_client_usage_expired(self) -> None:
        mgr = ClientManager()
        past = datetime.now(UTC) - timedelta(days=1)
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp", expires_at=past)
        with pytest.raises(ClientExpiredError):
            mgr.record_client_usage(client.id)

    def test_record_client_usage_revoked(self) -> None:
        mgr = ClientManager()
        client = mgr.create_client(sdk_id="sdk-1", name="MyApp")
        mgr.revoke_client(client.id)
        with pytest.raises(ClientExpiredError):
            mgr.record_client_usage(client.id)
