"""Integration layer — wiring the agent runtime into the EAIP kernel."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.agents.runtime import AgentRuntime
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from eaip.adapters.llm.base import LLMAdapter
    from eaip.events.bus import EventBus
    from eaip.metrics.metrics import Meter
    from eaip.runtime.kernel import RuntimeKernel


class AgentRuntimeModule:
    """Runtime module that registers the agent runtime with the EAIP kernel.

    Usage::

        module = AgentRuntimeModule(llm_adapter=my_adapter, tool_registry=my_registry)
        kernel.register_module("agents", module)
        # kernel.boot() will call module.start()
    """

    name: str = "agents"

    def __init__(  # noqa: D107
        self,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry | None = None,
        event_bus: EventBus | None = None,
        meter: Meter | None = None,
        **_kwargs: Any,
    ) -> None:
        self._llm_adapter = llm_adapter
        self._tool_registry = tool_registry or ToolRegistry()
        self._event_bus = event_bus
        self._meter = meter
        self._runtime: AgentRuntime | None = None
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.agents.integration")

    @property
    def runtime(self) -> AgentRuntime:
        """Return the underlying AgentRuntime."""
        if self._runtime is None:
            raise RuntimeError("AgentRuntime not initialized. Call start() first.")
        return self._runtime

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the agent runtime module.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        self._runtime = AgentRuntime(
            llm_adapter=self._llm_adapter,
            tool_registry=self._tool_registry,
            event_bus=self._event_bus,
            meter=self._meter,
        )

        await self._runtime.health()

        if kernel is not None:
            kernel.platform.health.register(self._name_check())
            kernel.platform.capabilities.register(self._name_capability())
            kernel.register_module("agent_runtime", self._runtime)

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the agent runtime module."""
        self._log.info("integration.stop")
        self._started = False

    def _name_check(self) -> HealthCheck:
        check_name = "agent_runtime"

        class _AgentHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _AgentHealthCheck()

    def _name_capability(self) -> Capability:
        return Capability(
            name="agent:runtime",
            title="Agent Runtime",
            status=CapabilityStatus.ENABLED,
            tags=("agent", "runtime"),
        )


def create_agent_runtime(
    llm_adapter: LLMAdapter,
    tool_registry: ToolRegistry | None = None,
    *,
    event_bus: EventBus | None = None,
    meter: Meter | None = None,
) -> AgentRuntime:
    """Create a fully wired AgentRuntime.

    Args:
        llm_adapter: The LLM adapter for planning and LLM steps.
        tool_registry: Optional tool registry (defaults to empty).
        event_bus: Optional event bus for publishing events.
        meter: Optional meter for metrics.

    Returns:
        A configured AgentRuntime.
    """
    return AgentRuntime(
        llm_adapter=llm_adapter,
        tool_registry=tool_registry or ToolRegistry(),
        event_bus=event_bus,
        meter=meter,
    )


__all__ = ["AgentRuntimeModule", "create_agent_runtime"]
