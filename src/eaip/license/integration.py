"""License & entitlement management runtime module."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.license.enforcement import LicenseEnforcer
from eaip.license.health import LicenseHealthCheck
from eaip.license.manager import LicenseManager
from eaip.license.models import LicenseConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class LicenseRuntimeModule:
    """Runtime module that wires license & entitlement management services.

    Implements the :class:`eaip.runtime.module.RuntimeModule` protocol.
    """

    name: str = "license"

    def __init__(
        self,
        config: LicenseConfig | None = None,
        manager: LicenseManager | None = None,
        enforcer: LicenseEnforcer | None = None,
    ) -> None:
        self._config = config or LicenseConfig()
        self._manager = manager or LicenseManager(config=self._config)
        self._enforcer = enforcer or LicenseEnforcer(self._manager)
        self._health_check = LicenseHealthCheck(self._manager)
        self._log = get_logger("eaip.license.integration")

    @property
    def config(self) -> LicenseConfig:
        return self._config

    @property
    def manager(self) -> LicenseManager:
        return self._manager

    @property
    def enforcer(self) -> LicenseEnforcer:
        return self._enforcer

    @property
    def health_check(self) -> LicenseHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("license.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.license",
            title="License & Entitlement Management",
            description=(
                "License key management with feature entitlements, "
                "usage tracking, quota enforcement, and validation"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("license", "entitlement", "enforcement", "quota"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)

        kernel.register_module("license.manager", self._manager)
        kernel.register_module("license.enforcer", self._enforcer)

        async def _event_forward(record: Any) -> None:
            with contextlib.suppress(Exception):
                await kernel.platform.events.publish(record)

        self._manager.set_event_callback(_event_forward)

        self._log.info("license.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        self._log.info("license.module.stopping")


__all__ = ["LicenseRuntimeModule"]
