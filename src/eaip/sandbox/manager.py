"""SandboxManager — manage environments and sandboxes."""

from __future__ import annotations

from datetime import timedelta

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.sandbox.events import (
    EnvironmentCreated,
    EnvironmentDeleted,
    SandboxCreated,
    SandboxExpired,
    SandboxStopped,
)
from eaip.sandbox.exceptions import (
    EnvironmentNotFoundError,
    SandboxNotFoundError,
)
from eaip.sandbox.models import (
    Environment,
    Sandbox,
    SandboxConfig,
    SandboxStatus,
)
from eaip.shared.time import utc_now


class SandboxManager:
    def __init__(self, config: SandboxConfig | None = None, event_bus: EventBus | None = None) -> None:
        self._config = config or SandboxConfig()
        self._environments: dict[str, Environment] = {}
        self._sandboxes: dict[str, Sandbox] = {}
        self._log = get_logger("eaip.sandbox.manager")
        self._event_bus = event_bus

    @property
    def config(self) -> SandboxConfig:
        return self._config

    async def create_environment(self, environment: Environment) -> Environment:
        self._environments[environment.id] = environment
        if self._event_bus is not None:
            await self._event_bus.publish(
                EnvironmentCreated(
                    environment_id=environment.id,
                    name=environment.name,
                    environment_type=environment.type.value,
                )
            )
        self._log.info("sandbox.environment.created", id=environment.id, name=environment.name)
        return environment

    async def get_environment(self, environment_id: str) -> Environment:
        env = self._environments.get(environment_id)
        if env is None:
            raise EnvironmentNotFoundError(f"Environment '{environment_id}' not found")
        return env

    async def list_environments(self) -> list[Environment]:
        return list(self._environments.values())

    async def delete_environment(self, environment_id: str) -> None:
        if environment_id not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{environment_id}' not found")
        del self._environments[environment_id]
        if self._event_bus is not None:
            await self._event_bus.publish(EnvironmentDeleted(environment_id=environment_id))
        self._log.info("sandbox.environment.deleted", id=environment_id)

    async def create_sandbox(self, sandbox: Sandbox) -> Sandbox:
        if sandbox.environment_id not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{sandbox.environment_id}' not found")
        expires_at = utc_now() + timedelta(minutes=sandbox.ttl_minutes)
        sandbox = sandbox.model_copy(
            update={"expires_at": expires_at, "status": SandboxStatus.RUNNING},
            deep=True,
        )
        self._sandboxes[sandbox.id] = sandbox
        if self._event_bus is not None:
            await self._event_bus.publish(
                SandboxCreated(
                    sandbox_id=sandbox.id,
                    name=sandbox.name,
                    environment_id=sandbox.environment_id,
                    template_id=sandbox.template_id,
                    ttl_minutes=sandbox.ttl_minutes,
                    expires_at=sandbox.expires_at,
                )
            )
        self._log.info("sandbox.sandbox.created", id=sandbox.id, name=sandbox.name)
        return sandbox

    async def get_sandbox(self, sandbox_id: str) -> Sandbox:
        sb = self._sandboxes.get(sandbox_id)
        if sb is None:
            raise SandboxNotFoundError(f"Sandbox '{sandbox_id}' not found")
        return sb

    async def list_sandboxes(self, environment_id: str | None = None) -> list[Sandbox]:
        if environment_id is not None:
            return [sb for sb in self._sandboxes.values() if sb.environment_id == environment_id]
        return list(self._sandboxes.values())

    async def stop_sandbox(self, sandbox_id: str, reason: str = "manual") -> Sandbox:
        sb = await self.get_sandbox(sandbox_id)
        sb = sb.model_copy(
            update={"status": SandboxStatus.STOPPED, "stopped_at": utc_now()},
            deep=True,
        )
        self._sandboxes[sandbox_id] = sb
        if self._event_bus is not None:
            await self._event_bus.publish(
                SandboxStopped(
                    sandbox_id=sandbox_id,
                    environment_id=sb.environment_id,
                    reason=reason,
                )
            )
        self._log.info("sandbox.sandbox.stopped", id=sandbox_id, reason=reason)
        return sb

    async def delete_sandbox(self, sandbox_id: str) -> None:
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(f"Sandbox '{sandbox_id}' not found")
        del self._sandboxes[sandbox_id]
        self._log.info("sandbox.sandbox.deleted", id=sandbox_id)

    async def expire_stale(self) -> list[Sandbox]:
        now = utc_now()
        expired: list[Sandbox] = []
        for sb_id, sb in list(self._sandboxes.items()):
            if sb.status == SandboxStatus.RUNNING and sb.expires_at < now:
                sb = sb.model_copy(
                    update={"status": SandboxStatus.EXPIRED, "stopped_at": now},
                    deep=True,
                )
                self._sandboxes[sb_id] = sb
                expired.append(sb)
                if self._event_bus is not None:
                    await self._event_bus.publish(
                        SandboxExpired(
                            sandbox_id=sb_id,
                            environment_id=sb.environment_id,
                            expires_at=sb.expires_at,
                        )
                    )
                self._log.info("sandbox.sandbox.expired", id=sb_id)
        return expired


__all__ = ["SandboxManager"]
