"""ClientManager — API client lifecycle management."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

import anyio

from eaip.logging.context import get_logger
from eaip.sdk.events import ClientCreated, ClientRevoked
from eaip.sdk.exceptions import ClientExpiredError, ClientNotFoundError
from eaip.sdk.models import ApiClient, ClientStatus
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.events.bus import EventBus


class ClientManager:
    """Manages API client registration, validation, and lifecycle."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._clients: dict[str, ApiClient] = {}
        self._log = get_logger("eaip.sdk.clients")
        self._event_bus = event_bus

    def create_client(
        self,
        sdk_id: str,
        name: str,
        config: dict[str, Any] | None = None,
        client_version: str = "1.0.0",
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApiClient:
        client_id = f"cli-{uuid.uuid4().hex[:12]}"
        now = utc_now()
        client = ApiClient(
            id=client_id,
            name=name,
            sdk_id=sdk_id,
            client_version=client_version,
            status=ClientStatus.ACTIVE,
            api_key_id=f"ak-{uuid.uuid4().hex[:16]}",
            configuration=config or {},
            last_used_at=None,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._clients[client_id] = client
        self._log.info("sdk.client.created", client_id=client_id, sdk_id=sdk_id)
        if self._event_bus is not None:
            anyio.from_thread.run(
                self._event_bus.publish,
                ClientCreated(client_id=client_id, sdk_id=sdk_id, name=name),
            )
        return client

    def get_client(self, client_id: str) -> ApiClient:
        if client_id not in self._clients:
            raise ClientNotFoundError(
                f"Client {client_id!r} not found",
                context={"client_id": client_id},
            )
        return self._clients[client_id]

    def revoke_client(self, client_id: str) -> ApiClient:
        client = self.get_client(client_id)
        revoked = client.model_copy(update={"status": ClientStatus.REVOKED})
        self._clients[client_id] = revoked
        self._log.info("sdk.client.revoked", client_id=client_id)
        if self._event_bus is not None:
            anyio.from_thread.run(
                self._event_bus.publish,
                ClientRevoked(client_id=client_id, sdk_id=client.sdk_id),
            )
        return revoked

    def validate_client(self, client_id: str, api_key: str) -> bool:
        try:
            client = self.get_client(client_id)
        except ClientNotFoundError:
            return False

        if client.status is ClientStatus.REVOKED:
            return False

        if client.status is ClientStatus.EXPIRED:
            return False

        if client.expires_at is not None and utc_now() > client.expires_at:
            expired = client.model_copy(update={"status": ClientStatus.EXPIRED})
            self._clients[client_id] = expired
            return False

        return client.api_key_id == api_key

    def list_clients(self, sdk_id: str) -> Sequence[ApiClient]:
        return [c for c in self._clients.values() if c.sdk_id == sdk_id]

    def update_client(self, client_id: str, config: dict[str, Any] | None = None) -> ApiClient:
        client = self.get_client(client_id)
        updated = client.model_copy(update={"configuration": config or {}})
        self._clients[client_id] = updated
        self._log.info("sdk.client.updated", client_id=client_id)
        return updated

    def record_client_usage(self, client_id: str) -> None:
        client = self.get_client(client_id)
        if client.expires_at is not None and utc_now() > client.expires_at:
            expired = client.model_copy(update={"status": ClientStatus.EXPIRED})
            self._clients[client_id] = expired
            raise ClientExpiredError(
                f"Client {client_id!r} has expired",
                context={"client_id": client_id},
            )
        if client.status is ClientStatus.EXPIRED:
            raise ClientExpiredError(
                f"Client {client_id!r} has expired",
                context={"client_id": client_id},
            )
        if client.status is ClientStatus.REVOKED:
            raise ClientExpiredError(
                f"Client {client_id!r} has been revoked",
                context={"client_id": client_id},
            )
        updated = client.model_copy(update={"last_used_at": utc_now()})
        self._clients[client_id] = updated
