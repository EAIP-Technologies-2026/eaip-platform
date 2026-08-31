"""Runtime integration — ProviderRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityContract
from eaip.logging.context import get_logger
from eaip.providers.base import Provider
from eaip.providers.discovery import ProviderDiscovery
from eaip.providers.health import ProviderHealthCheck, ProviderHealthMonitor
from eaip.providers.models import ProviderInstance
from eaip.providers.registry import ProviderRegistry
from eaip.providers.selector import ProviderSelector

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ProviderRuntimeModule:
    """RuntimeModule that manages AI providers during kernel boot.

    - On start: registers known providers, discovers models,
      creates ProviderSelector, registers provider capabilities,
      and starts health monitoring.
    - On stop: stops health monitoring, disables providers.
    """

    name: str = "providers"

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        discovery: ProviderDiscovery | None = None,
    ) -> None:
        """Initialize the ProviderRuntimeModule.

        Args:
            registry: Optional provider registry.
            discovery: Optional provider discovery service.
        """
        self._registry = registry or ProviderRegistry()
        self._discovery = discovery or ProviderDiscovery(self._registry)
        self._providers: dict[str, Provider] = {}
        self._selector: ProviderSelector | None = None
        self._monitor: ProviderHealthMonitor | None = None
        self._log = get_logger("eaip.runtime.provider_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        """Return the last provider startup duration in seconds."""
        return self._startup_duration

    @property
    def registry(self) -> ProviderRegistry:
        """Return the provider registry."""
        return self._registry

    @property
    def selector(self) -> ProviderSelector:
        """Return the ProviderSelector, raising if not yet started."""
        if self._selector is None:
            raise RuntimeError("ProviderSelector not available until start() is called")
        return self._selector

    def register_provider(self, name: str, provider: Provider) -> None:
        """Register a Provider instance for routing.

        Args:
            name: The provider name (must match a ProviderInstance name).
            provider: The Provider implementation.
        """
        self._providers[name] = provider

    async def start(self, kernel: RuntimeKernel) -> None:
        """Initialise the provider subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("provider.module.start")
        t0 = time.monotonic()

        self._selector = ProviderSelector(self._registry, self._providers)

        for inst in self._registry.all():
            await self._register_capability(kernel, inst)

        check = ProviderHealthCheck(self._registry)
        kernel.platform.health.register(check)

        self._monitor = ProviderHealthMonitor(self._registry, interval_seconds=60.0)
        await self._monitor.start()

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "provider.module.complete",
            providers=len(self._registry),
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the provider subsystem.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("provider.module.stop")
        if self._monitor is not None:
            await self._monitor.stop()
        self._log.info("provider.module.stopped")

    async def _register_capability(
        self,
        kernel: RuntimeKernel,
        instance: ProviderInstance,
    ) -> None:
        """Register a capability for each model the provider offers."""
        for mc in instance.models:
            features = ", ".join(f.value for f in mc.features)
            cap = Capability(
                name=f"provider:{instance.name}:{mc.model_id}",
                title=f"{instance.name}/{mc.model_id}",
                description=f"AI model {mc.model_id} via {instance.name} "
                f"(features: {features}, context: {mc.context_window})",
                version="1.0.0",
                tags=("provider", instance.name, mc.model_id),
                provides=(f"model:{mc.model_id}",),
                contract=CapabilityContract(
                    contract_version="1.0.0",
                    event_schemas={
                        "eaip.provider.request_started": "1.0",
                        "eaip.provider.request_completed": "1.0",
                    },
                ),
                metadata={
                    "provider_type": instance.provider_type,
                    "model_id": mc.model_id,
                    "context_window": str(mc.context_window),
                    "max_tokens": str(mc.max_tokens),
                    "features": features,
                },
            )
            try:
                kernel.platform.capabilities.register(cap)
            except Exception:
                self._log.warning(
                    "provider.capability.register_failed",
                    capability=cap.name,
                )


__all__ = ["ProviderRuntimeModule"]
