"""Real connector adapter abstract base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConnectionStatus(StrEnum):
    """Status of a connector connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    ERROR = "error"
    SYNTHETIC = "synthetic"


class ConnectorHealthResult(BaseModel):
    """Health check result from a real connector adapter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str
    status: ConnectionStatus
    healthy: bool
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: Any = Field(default_factory=utc_now)


class ConnectorCapability(BaseModel):
    """Capability discovered from a real connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    operations: list[str] = Field(default_factory=list)
    data_classes: list[str] = Field(default_factory=list)
    permissions_required: list[str] = Field(default_factory=list)


class RealConnectorAdapter(ABC):
    """Abstract base for real connector adapters.

    Each adapter wraps a specific external system (Salesforce, Slack, etc.)
    and provides a uniform interface for connect/discover/invoke/health.

    When credentials are not configured, adapters MUST return SYNTHETIC mode
    and never pretend to be connected.
    """

    connector_type: str = ""
    display_name: str = ""
    supported_transports: tuple[str, ...] = ("http",)
    default_operations: tuple[str, ...] = ()

    def __init__(self, connector_id: str, tenant_id: str) -> None:
        self.connector_id = connector_id
        self.tenant_id = tenant_id
        self._connection: Any = None
        self._status = ConnectionStatus.DISCONNECTED
        self._credentials_ref: str = ""

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def is_synthetic(self) -> bool:
        return self._status == ConnectionStatus.SYNTHETIC

    @abstractmethod
    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        """Connect using a vault:// credential reference.

        If credentials_ref is empty or invalid, MUST set status to SYNTHETIC.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        ...

    @abstractmethod
    async def discover(self) -> list[ConnectorCapability]:
        """Discover available capabilities from the external system."""
        ...

    @abstractmethod
    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """Invoke an operation on the external system."""
        ...

    @abstractmethod
    async def health(self) -> ConnectorHealthResult:
        """Check health of the connection."""
        ...

    def _validate_credentials_ref(self, credentials_ref: str) -> bool:
        """Validate that a credential reference is a vault:// reference."""
        if not credentials_ref:
            return False
        if not credentials_ref.startswith("vault://"):
            return False
        return True

    def _synthetic_result(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """Return a synthetic result when not connected."""
        return {
            "mode": "SYNTHETIC",
            "connector_id": self.connector_id,
            "connector_type": self.connector_type,
            "operation": operation,
            "params": params,
            "message": f"Synthetic response for {operation} — no real credentials configured",
        }
