"""Service registry for managing service instances and heartbeats."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.mesh.events import (
    ServiceHealthChanged,
    ServiceRegistered,
    ServiceUnregistered,
)
from eaip.mesh.exceptions import NoHealthyInstanceError, ServiceNotFoundError
from eaip.mesh.models import ServiceInstance, ServiceStatus


class ServiceRegistry:
    """In-memory service registry with heartbeat expiry detection."""

    def __init__(self, event_bus: Any = None) -> None:
        self._instances: dict[str, ServiceInstance] = {}
        self._log = get_logger("eaip.mesh.registry")
        self._event_bus = event_bus

    def register(self, instance: ServiceInstance) -> ServiceInstance:
        self._instances.get(instance.id)
        self._instances[instance.id] = instance
        self._log.info("service.registered", id=instance.id, name=instance.name)
        if self._event_bus is not None:
            self._event_bus.publish(
                ServiceRegistered(service_id=instance.id, service_name=instance.name)
            )
        return instance

    def unregister(self, instance_id: str) -> None:
        instance = self._instances.pop(instance_id, None)
        if instance is None:
            raise ServiceNotFoundError(f"Service instance {instance_id!r} not found.")
        self._log.info("service.unregistered", id=instance_id, name=instance.name)
        if self._event_bus is not None:
            self._event_bus.publish(
                ServiceUnregistered(service_id=instance_id, service_name=instance.name)
            )

    def get_instance(self, instance_id: str) -> ServiceInstance:
        instance = self._instances.get(instance_id)
        if instance is None:
            raise ServiceNotFoundError(f"Service instance {instance_id!r} not found.")
        return instance

    def list_instances(self, service_name: str | None = None) -> list[ServiceInstance]:
        if service_name is None:
            return list(self._instances.values())
        return [i for i in self._instances.values() if i.name == service_name]

    def heartbeat(self, instance_id: str) -> ServiceInstance:
        instance = self.get_instance(instance_id)
        import datetime

        updated = instance.model_copy(
            update={"last_heartbeat": datetime.datetime.now(datetime.UTC)}
        )
        self._instances[instance_id] = updated
        if updated.status is ServiceStatus.UNKNOWN or updated.status is ServiceStatus.DOWN:
            self._update_status(instance_id, ServiceStatus.UP)
        return self._instances[instance_id]

    def check_expired(self, timeout_seconds: float = 30.0) -> list[ServiceInstance]:
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        expired: list[ServiceInstance] = []
        for inst in list(self._instances.values()):
            elapsed = (now - inst.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                self._update_status(inst.id, ServiceStatus.DOWN)
                expired.append(self._instances[inst.id])
        return expired

    def get_healthy_instances(self, service_name: str) -> list[ServiceInstance]:
        instances = self.list_instances(service_name)
        healthy = [i for i in instances if i.status is ServiceStatus.UP]
        if not healthy:
            raise NoHealthyInstanceError(
                f"No healthy instances found for service {service_name!r}.",
                context={"service_name": service_name},
            )
        return healthy

    def list_services(self) -> list[str]:
        return list({i.name for i in self._instances.values()})

    def _update_status(self, instance_id: str, new_status: ServiceStatus) -> None:
        instance = self._instances.get(instance_id)
        if instance is None or instance.status is new_status:
            return
        old_status = instance.status
        updated = instance.model_copy(update={"status": new_status})
        self._instances[instance_id] = updated
        self._log.info(
            "service.status_changed",
            id=instance_id,
            name=instance.name,
            old=old_status.value,
            new=new_status.value,
        )
        if self._event_bus is not None:
            self._event_bus.publish(
                ServiceHealthChanged(
                    service_id=instance_id,
                    service_name=instance.name,
                    old_status=old_status,
                    new_status=new_status,
                )
            )


__all__ = ["ServiceRegistry"]
