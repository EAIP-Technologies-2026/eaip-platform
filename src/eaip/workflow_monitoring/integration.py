"""RuntimeKernel integration — registers WorkflowMonitor as a RuntimeModule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.workflow_monitoring.health import WorkflowMonitorHealthCheck
from eaip.workflow_monitoring.service import WorkflowMonitorService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WorkflowMonitorRuntimeModule:
    """RuntimeModule that registers the workflow monitoring subsystem with the kernel.

    On start, registers the monitor service, health checks, and capabilities.
    On stop, performs cleanup.
    """

    name: str = "workflow_monitoring"

    def __init__(
        self,
        service: WorkflowMonitorService | None = None,
    ) -> None:
        """Initialize WorkflowMonitorRuntimeModule.

        Args:
            service: An optional WorkflowMonitorService instance.
        """
        self._service = service or WorkflowMonitorService()
        self._health_check = WorkflowMonitorHealthCheck(service=self._service)
        self._log = get_logger("eaip.workflow_monitoring.integration")

    @property
    def service(self) -> WorkflowMonitorService:
        """Return the underlying WorkflowMonitorService."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register health checks and capabilities with the kernel platform.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("workflow_monitoring.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="workflow_monitoring:engine",
                title="Workflow Monitoring Engine",
                status=CapabilityStatus.ENABLED,
                tags=("workflow_monitoring", "engine"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="workflow_monitoring:dashboard",
                title="Workflow Monitoring Dashboard",
                status=CapabilityStatus.ENABLED,
                tags=("workflow_monitoring", "dashboard"),
            )
        )

        kernel.register_module("workflow_monitoring.service", self._service)

        self._log.info("workflow_monitoring.module.complete")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Clean up workflow monitoring resources on shutdown.

        Args:
            _kernel: The runtime kernel (unused).
        """
        self._log.info("workflow_monitoring.module.stop")


__all__ = ["WorkflowMonitorRuntimeModule"]
