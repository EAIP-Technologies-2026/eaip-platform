from __future__ import annotations

import asyncio
import sys

import uvicorn

from eaip._version import __version__
from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app
from eaip.logging.context import get_logger

_asyncio_loop: asyncio.AbstractEventLoop | None = None


async def _async_main() -> None:
    global _asyncio_loop
    _asyncio_loop = asyncio.get_running_loop()

    log = get_logger("eaip.__main__")

    builder = ApplicationBuilder()
    lifecycle = builder.build()

    await lifecycle.start()

    container = lifecycle.platform.container
    events = lifecycle.platform.events
    metrics_meter = container.try_resolve("Meter")  # noqa: F841

    # ------------------------------------------------------------------
    # Register core service instances into the DI container
    # ------------------------------------------------------------------

    # Agent services
    from eaip.agents.registry import AgentRegistry
    from eaip.agents.runtime import AgentRuntime

    agent_registry = AgentRegistry(event_bus=events)
    container.register_instance(AgentRegistry, agent_registry)

    agent_runtime = AgentRuntime(
        llm_adapter=None,
        tool_registry=None,
        event_bus=events,
    )
    container.register_instance(AgentRuntime, agent_runtime)

    # Auth services
    from eaip.auth.auth_providers import AuthenticationService
    from eaip.auth.tokens import TokenService

    auth_service = AuthenticationService(secret="eaip-dev-secret-do-not-use-in-production", event_bus=events)
    container.register_instance(AuthenticationService, auth_service)

    # Workflow services
    from eaip.workflow.executor import WorkflowEngine
    from eaip.workflow.registry import WorkflowRegistry

    wf_registry = WorkflowRegistry(event_bus=events)
    container.register_instance(WorkflowRegistry, wf_registry)

    wf_engine = WorkflowEngine(event_bus=events)
    container.register_instance(WorkflowEngine, wf_engine)

    # Mission services
    from eaip.runtime.mission import MissionRegistry

    mission_registry = MissionRegistry(event_bus=events)
    container.register_instance(MissionRegistry, mission_registry)

    # WebSocket services
    from eaip.ws.channel_manager import ChannelManager
    from eaip.ws.connection_manager import ConnectionManager
    from eaip.ws.push_service import PushService

    conn_mgr = ConnectionManager()
    channel_mgr = ChannelManager()
    push_svc = PushService(channel_manager=channel_mgr, connection_manager=conn_mgr)
    container.register_instance(ConnectionManager, conn_mgr)
    container.register_instance(ChannelManager, channel_mgr)
    container.register_instance(PushService, push_svc)

    # Knowledge services
    from eaip.knowledge.engine import KnowledgeEngine
    from eaip.knowledge.registry import KnowledgeRegistry as KR

    knowledge_registry = KR()

    def _publish_event(event):
        try:
            if _asyncio_loop and not _asyncio_loop.is_closed():
                _asyncio_loop.create_task(events.publish(event))
        except (RuntimeError, Exception):
            pass

    knowledge_engine = KnowledgeEngine(
        knowledge_registry,
        knowledge_registry,
        None,
        event_publisher=_publish_event,
    )
    container.register_instance(KR, knowledge_registry)
    container.register_instance(KnowledgeEngine, knowledge_engine)

    log.info("services.registered", count=len(container._providers))

    # ------------------------------------------------------------------

    app = create_app(lifecycle)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        ws="auto",
    )
    server = uvicorn.Server(config)

    log.info("http.server.starting", host="0.0.0.0", port=8080)

    try:
        await server.serve()
    finally:
        await lifecycle.stop()


def main() -> None:
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"eaip {__version__}")
        sys.exit(0)
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
