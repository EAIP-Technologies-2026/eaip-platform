"""Health check for the service mesh subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.mesh.registry import ServiceRegistry
from eaip.mesh.routing import ServiceRouter


class MeshHealthCheck(HealthCheck):
    """Reports mesh health including registry and router status."""

    name: str = "mesh"

    def __init__(
        self,
        registry: ServiceRegistry | None = None,
        router: ServiceRouter | None = None,
    ) -> None:
        self._registry = registry
        self._router = router

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        children: list[HealthReport] = []

        if self._registry is not None:
            try:
                services = self._registry.list_services()
                instances = self._registry.list_instances()
                registry_status = HealthStatus.HEALTHY
                details["registry_services"] = len(services)
                details["registry_instances"] = len(instances)
            except Exception as exc:
                registry_status = HealthStatus.DEGRADED
                details["registry_error"] = str(exc)
            children.append(
                HealthReport(
                    component="mesh.registry",
                    status=registry_status,
                    details=details,
                )
            )

        if self._router is not None:
            try:
                routes = self._router.list_routes()
                router_status = HealthStatus.HEALTHY
                details["routes"] = len(routes)
            except Exception as exc:
                router_status = HealthStatus.DEGRADED
                details["router_error"] = str(exc)
            children.append(
                HealthReport(
                    component="mesh.router",
                    status=router_status,
                    details={"routes_count": len(self._router.list_routes())},
                )
            )

        overall = (
            HealthStatus.HEALTHY
            if all(c.status is HealthStatus.HEALTHY for c in children)
            else HealthStatus.DEGRADED
        )

        return HealthReport(
            component="mesh",
            status=overall,
            message="Service mesh health check",
            details=details,
            children=tuple(children),
        )


__all__ = ["MeshHealthCheck"]
