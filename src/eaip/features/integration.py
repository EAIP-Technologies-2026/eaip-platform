"""Feature flag & experimentation engine runtime module."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.features.experiments import ExperimentService
from eaip.features.health import FeatureHealthCheck
from eaip.features.manager import FeatureManager
from eaip.features.models import FeatureConfig
from eaip.features.rollout import RolloutManager
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FeatureRuntimeModule:
    """Runtime module that wires feature flag & experimentation services.

    Implements the :class:`eaip.runtime.module.RuntimeModule` protocol.
    """

    name: str = "features"

    def __init__(
        self,
        config: FeatureConfig | None = None,
        manager: FeatureManager | None = None,
        experiment_service: ExperimentService | None = None,
        rollout_manager: RolloutManager | None = None,
    ) -> None:
        self._config = config or FeatureConfig()
        self._manager = manager or FeatureManager()
        self._experiment_service = experiment_service or ExperimentService()
        self._rollout_manager = rollout_manager or RolloutManager(self._manager)
        self._health_check = FeatureHealthCheck(self._manager)
        self._log = get_logger("eaip.features.integration")

    @property
    def config(self) -> FeatureConfig:
        return self._config

    @property
    def manager(self) -> FeatureManager:
        return self._manager

    @property
    def experiment_service(self) -> ExperimentService:
        return self._experiment_service

    @property
    def rollout_manager(self) -> RolloutManager:
        return self._rollout_manager

    @property
    def health_check(self) -> FeatureHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("features.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.features",
            title="Feature Flag & Experimentation Engine",
            description=(
                "Feature flag management with gradual rollout, "
                "A/B testing, and experiment telemetry"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("features", "flags", "experiments", "rollout", "a/b-testing"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)

        kernel.register_module("features.manager", self._manager)
        kernel.register_module("features.experiment_service", self._experiment_service)
        kernel.register_module("features.rollout_manager", self._rollout_manager)

        async def _event_forward(record: Any) -> None:
            with contextlib.suppress(Exception):
                await kernel.platform.events.publish(record)

        self._manager.set_event_callback(_event_forward)
        self._experiment_service.set_event_callback(_event_forward)
        self._rollout_manager.set_event_callback(_event_forward)

        self._log.info("features.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        self._log.info("features.module.stopping")


__all__ = ["FeatureRuntimeModule"]
