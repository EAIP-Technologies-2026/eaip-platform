"""Geo-IP runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.geoip.health import GeoIPHealthCheck
from eaip.geoip.models import GeoIPConfig
from eaip.geoip.service import GeoIPService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GeoIPRuntimeModule:
    name: str = "geoip"

    def __init__(
        self,
        config: GeoIPConfig | None = None,
        service: GeoIPService | None = None,
    ) -> None:
        self._config = config or GeoIPConfig()
        self._service = service or GeoIPService(config=self._config)
        self._health_check = GeoIPHealthCheck(self._service)
        self._log = get_logger("eaip.geoip.integration")

    @property
    def config(self) -> GeoIPConfig:
        return self._config

    @property
    def service(self) -> GeoIPService:
        return self._service

    @property
    def health_check(self) -> GeoIPHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("geoip.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.geoip",
            title="Geo-IP Service",
            description=(
                "IP geolocation lookup, geo-blocking enforcement, cache management, and enrichment"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("geoip", "geolocation", "geo-blocking", "enrichment"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("geoip.service", self._service)
        self._log.info("geoip.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("geoip.module.stopping")


__all__ = ["GeoIPRuntimeModule"]
