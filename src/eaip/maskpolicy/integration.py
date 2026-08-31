"""Runtime integration — MaskPolicyRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.maskpolicy.engine import MaskingPolicyEngine
from eaip.maskpolicy.health import MaskPolicyHealthCheck
from eaip.maskpolicy.models import MaskingConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.maskpolicy.integration")


class MaskPolicyRuntimeModule:
    name: str = "maskpolicy"

    def __init__(
        self,
        config: MaskingConfig | None = None,
        engine: MaskingPolicyEngine | None = None,
    ) -> None:
        self._config = config or MaskingConfig()
        self._engine = engine or MaskingPolicyEngine(config=self._config)
        self._health_check = MaskPolicyHealthCheck(engine=self._engine)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.maskpolicy",
            title="Data Masking Policy Engine",
            description="Manage masking policies and rules for data protection",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("maskpolicy", "masking", "policy", "data-protection"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info("maskpolicy_module_started", engine_ready=True)

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("maskpolicy_module_stopped")

    @property
    def engine(self) -> MaskingPolicyEngine:
        return self._engine

    @property
    def health_check(self) -> MaskPolicyHealthCheck:
        return self._health_check


__all__ = ["MaskPolicyRuntimeModule"]
