"""Load balancer with multiple strategies for service instance selection."""

from __future__ import annotations

import random
from typing import Any

from eaip.logging.context import get_logger
from eaip.mesh.events import LoadBalanced
from eaip.mesh.exceptions import LoadBalancerError
from eaip.mesh.models import LoadBalancerState, RoutingStrategy, ServiceInstance


class LoadBalancer:
    """Distributes requests across service instances using configurable strategies."""

    def __init__(self, event_bus: Any = None) -> None:
        self._states: dict[str, LoadBalancerState] = {}
        self._log = get_logger("eaip.mesh.load_balancer")
        self._event_bus = event_bus

    def _get_state(self, service_name: str, strategy: RoutingStrategy) -> LoadBalancerState:
        if service_name not in self._states:
            self._states[service_name] = LoadBalancerState(
                service_name=service_name,
                strategy=strategy,
            )
        return self._states[service_name]

    def get_next_instance(
        self,
        service_name: str,
        instances: list[ServiceInstance],
        strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
    ) -> ServiceInstance:
        if not instances:
            raise LoadBalancerError(
                f"No instances available for service {service_name!r}.",
                context={"service_name": service_name, "strategy": strategy.value},
            )

        fn = {
            RoutingStrategy.ROUND_ROBIN: self._round_robin,
            RoutingStrategy.RANDOM: self._random,
            RoutingStrategy.WEIGHTED: self._weighted,
            RoutingStrategy.LEAST_CONNECTIONS: self._least_connections,
        }.get(strategy)

        if fn is None:
            raise LoadBalancerError(f"Unknown strategy {strategy!r}.")

        state = self._get_state(service_name, strategy)
        instance = fn(instances, state)
        current_state = self._states[service_name]
        self._states[service_name] = current_state.model_copy(
            update={"last_distribution": instance.id}
        )

        if self._event_bus is not None:
            self._event_bus.publish(
                LoadBalanced(
                    service_name=service_name,
                    strategy=strategy,
                    selected_instance_id=instance.id,
                )
            )

        return instance

    def update_connections(
        self, instance_id: str, delta: int = 1, service_name: str | None = None
    ) -> None:
        if service_name is not None:
            if service_name not in self._states:
                self._states[service_name] = LoadBalancerState(
                    service_name=service_name,
                )
            states_to_update = [self._states[service_name]]
        else:
            states_to_update = list(self._states.values())
        for state in states_to_update:
            current = state.active_connections.get(instance_id, 0)
            new_conns = dict(state.active_connections)
            updated = current + delta
            if updated <= 0:
                new_conns.pop(instance_id, None)
            else:
                new_conns[instance_id] = updated
            self._states[state.service_name] = state.model_copy(
                update={"active_connections": new_conns}
            )

    def _round_robin(
        self, instances: list[ServiceInstance], state: LoadBalancerState
    ) -> ServiceInstance:
        idx = state.current_index % len(instances)
        self._states[state.service_name] = state.model_copy(update={"current_index": idx + 1})
        return instances[idx]

    def _random(
        self, instances: list[ServiceInstance], _state: LoadBalancerState
    ) -> ServiceInstance:
        return random.choice(instances)

    def _weighted(
        self, instances: list[ServiceInstance], _state: LoadBalancerState
    ) -> ServiceInstance:
        total = sum(i.weight for i in instances)
        r = random.uniform(0, total)
        cumulative = 0
        for inst in instances:
            cumulative += inst.weight
            if r <= cumulative:
                return inst
        return instances[-1]

    def _least_connections(
        self, instances: list[ServiceInstance], state: LoadBalancerState
    ) -> ServiceInstance:
        def conn_count(inst: ServiceInstance) -> int:
            return state.active_connections.get(inst.id, 0)

        return min(instances, key=conn_count)


__all__ = ["LoadBalancer"]
