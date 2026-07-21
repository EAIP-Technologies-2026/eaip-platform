"""KnowledgePermissionHealthCheck — reports the health of the knowledge permission subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.knowledge_permissions.service import KnowledgePermissionService


class KnowledgePermissionHealthCheck(HealthCheck):
    """Health check for the knowledge permission subsystem."""

    name: str = "knowledge_permissions"

    def __init__(self, service: KnowledgePermissionService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        cfg = self._service.config
        details = {
            "enabled": cfg.enabled,
            "total_permissions": len(self._service.list_permissions()),
            "total_rules": len(self._service.list_access_rules()),
            "total_roles": len(self._service.list_roles()),
            "total_assignments": len(self._service.list_assignments()),
            "audit_enabled": cfg.audit_enabled,
            "role_based_enabled": cfg.role_based_enabled,
            "acl_enabled": cfg.acl_enabled,
        }

        if not cfg.enabled:
            return HealthReport(
                component="knowledge_permissions",
                status=HealthStatus.DEGRADED,
                message="Knowledge permissions subsystem is disabled",
                details=details,
            )

        return HealthReport(
            component="knowledge_permissions",
            status=HealthStatus.HEALTHY,
            message="Knowledge permissions subsystem is operational",
            details=details,
        )


__all__ = ["KnowledgePermissionHealthCheck"]
