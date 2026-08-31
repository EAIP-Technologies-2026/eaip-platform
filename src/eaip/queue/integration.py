"""Runtime integration — QueueRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.queue.health import QueueHealthCheck
from eaip.queue.manager import QueueManager
from eaip.queue.models import QueueConfig
from eaip.queue.provider import MessageQueue

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class QueueRuntimeModule:
    """RuntimeModule that registers queue capabilities with the kernel."""

    name: str = "queue"

    def __init__(self, event_bus: Any = None) -> None:
        """Initialize the queue runtime module."""
        self._event_bus = event_bus
        self._manager = QueueManager(event_bus=event_bus)
        self._health_check = QueueHealthCheck()
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.queue.integration")

    def create_queue(self, config: QueueConfig) -> MessageQueue:
        """Create a queue and register it for health monitoring."""
        queue = self._manager.create_queue(config)
        self._health_check.register_queue(queue)
        return queue

    @property
    def manager(self) -> QueueManager:
        """Return the underlying queue manager."""
        return self._manager

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the queue module and register capabilities with the kernel."""
        t0 = time.monotonic()
        self._log.info("queue.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="queue:framework",
                title="Message Queue Framework",
                status=CapabilityStatus.ENABLED,
                tags=("queue", "messaging", "async"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "queue.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the queue module and close all queues."""
        self._log.info("queue.module.stop")
        await self._manager.close_all()
