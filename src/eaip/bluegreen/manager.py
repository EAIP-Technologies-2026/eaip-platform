"""BlueGreenManager — manage zero-downtime deployments with blue-green strategy."""

from __future__ import annotations

from eaip.bluegreen.events import (
    HealthCheckFailed,
    SwitchCompleted,
    SwitchRolledBack,
    SwitchStarted,
)
from eaip.bluegreen.exceptions import BlueGreenError, SwitchError
from eaip.bluegreen.models import (
    BlueGreenConfig,
    DeploymentSwitch,
    Environment,
    EnvironmentStatus,
    SwitchStrategy,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class BlueGreenManager:
    """Central service for managing blue-green deployments."""

    def __init__(
        self, config: BlueGreenConfig | None = None, event_bus: EventBus | None = None
    ) -> None:
        self._config = config or BlueGreenConfig()
        self._environments: dict[str, Environment] = {}
        self._switches: dict[str, DeploymentSwitch] = {}
        self._log = get_logger("eaip.bluegreen.manager")
        self._event_bus = event_bus

    @property
    def config(self) -> BlueGreenConfig:
        return self._config

    async def register_environment(self, env: Environment) -> Environment:
        """Register a deployment environment."""
        self._environments[env.id] = env
        self._log.info("bluegreen.env.registered", env_id=env.id, name=env.name)
        return env

    async def get_environment(self, env_id: str) -> Environment:
        """Retrieve an environment by ID."""
        env = self._environments.get(env_id)
        if env is None:
            raise BlueGreenError(f"Environment '{env_id}' not found")
        return env

    async def list_environments(self) -> list[Environment]:
        """List all registered environments."""
        return list(self._environments.values())

    async def get_active_environment(self) -> Environment | None:
        """Return the currently active environment, if any."""
        for env in self._environments.values():
            if env.status == EnvironmentStatus.ACTIVE:
                return env
        return None

    async def start_switch(
        self,
        from_env_id: str,
        to_env_id: str,
        strategy: SwitchStrategy = SwitchStrategy.HEALTH_CHECK,
    ) -> DeploymentSwitch:
        """Initiate a traffic switch between environments."""
        from_env = await self.get_environment(from_env_id)
        to_env = await self.get_environment(to_env_id)

        if from_env.status != EnvironmentStatus.ACTIVE:
            raise SwitchError(f"Source environment '{from_env_id}' is not active")
        if to_env.status != EnvironmentStatus.STANDBY:
            raise SwitchError(f"Target environment '{to_env_id}' is not in standby")

        switch = DeploymentSwitch(
            id=f"sw_{utc_now().timestamp():.0f}",
            from_env=from_env_id,
            to_env=to_env_id,
            strategy=strategy,
        )
        self._switches[switch.id] = switch

        if self._event_bus is not None:
            await self._event_bus.publish(
                SwitchStarted(
                    switch_id=switch.id,
                    from_env=from_env_id,
                    to_env=to_env_id,
                    strategy=strategy.value,
                )
            )
        self._log.info(
            "bluegreen.switch.started",
            switch_id=switch.id,
            from_env=from_env_id,
            to_env=to_env_id,
        )
        return switch

    async def complete_switch(self, switch_id: str) -> DeploymentSwitch:
        """Complete a traffic switch successfully."""
        switch = self._switches.get(switch_id)
        if switch is None:
            raise SwitchError(f"Switch '{switch_id}' not found")

        from_env = await self.get_environment(switch.from_env)
        to_env = await self.get_environment(switch.to_env)

        from_env = from_env.model_copy(update={"status": EnvironmentStatus.DRAINING}, deep=True)
        to_env = to_env.model_copy(update={"status": EnvironmentStatus.ACTIVE}, deep=True)
        self._environments[from_env.id] = from_env
        self._environments[to_env.id] = to_env

        if self._event_bus is not None:
            await self._event_bus.publish(
                SwitchCompleted(
                    switch_id=switch_id,
                    from_env=switch.from_env,
                    to_env=switch.to_env,
                    new_active=switch.to_env,
                )
            )
        self._log.info("bluegreen.switch.completed", switch_id=switch_id)
        return switch

    async def rollback_switch(self, switch_id: str, reason: str) -> DeploymentSwitch:
        """Roll back a traffic switch."""
        switch = self._switches.get(switch_id)
        if switch is None:
            raise SwitchError(f"Switch '{switch_id}' not found")

        if self._event_bus is not None:
            await self._event_bus.publish(
                SwitchRolledBack(
                    switch_id=switch_id,
                    from_env=switch.from_env,
                    to_env=switch.to_env,
                    reason=reason,
                )
            )
        self._log.info("bluegreen.switch.rolled_back", switch_id=switch_id, reason=reason)
        return switch

    async def report_health_failure(self, switch_id: str, environment: str, message: str) -> None:
        """Report a health check failure during a switch."""
        if self._event_bus is not None:
            await self._event_bus.publish(
                HealthCheckFailed(
                    switch_id=switch_id,
                    environment=environment,
                    message=message,
                )
            )
        self._log.warning(
            "bluegreen.health_check.failed",
            switch_id=switch_id,
            environment=environment,
        )

    async def get_switch(self, switch_id: str) -> DeploymentSwitch:
        """Retrieve a switch by ID."""
        switch = self._switches.get(switch_id)
        if switch is None:
            raise SwitchError(f"Switch '{switch_id}' not found")
        return switch

    async def list_switches(self) -> list[DeploymentSwitch]:
        """List all deployment switches."""
        return list(self._switches.values())


__all__ = ["BlueGreenManager"]
