"""Governance — permission and risk tiers for Conductor's governed tools."""

from __future__ import annotations

from typing import Any, ClassVar, Protocol, runtime_checkable

from eaip.copilot.models import RiskTier


@runtime_checkable
class GovernedTool(Protocol):
    """A platform tool that additionally declares governance attributes."""

    name: str
    description: str
    risk: RiskTier
    permission: str

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the provided keyword arguments."""


def tool_risk(tool: Any) -> RiskTier:
    """Return the risk tier declared on a tool, defaulting to informational."""
    return getattr(tool, "risk", RiskTier.INFORMATIONAL)


def tool_permission(tool: Any) -> str:
    """Return the permission required to invoke a tool."""
    return getattr(tool, "permission", f"copilot:{tool.name}")


class GovernancePolicy:
    """Decides whether a user may invoke a tool and whether approval is needed.

    Permissions are derived from the caller's roles. A role carrying the
    wildcard permission ``*`` may invoke any tool. Any tool whose risk tier is
    ACTION or higher always requires an explicit human approval before it runs.
    """

    _ROLE_PERMISSIONS: ClassVar[dict[str, frozenset[str]]] = {
        "admin": frozenset({"*"}),
        "user": frozenset(
            {
                "copilot:read",
                "copilot:tools:system_health",
                "copilot:tools:list_agents",
                "copilot:tools:list_workflows",
                "copilot:tools:knowledge_search",
                "copilot:memory:read",
                "copilot:memory:write",
                "copilot:memory:delete",
                "copilot:investigations:read",
                "copilot:investigations:write",
                "copilot:orchestration:read",
                "copilot:orchestration:write",
                "copilot:orchestration:execute",
            }
        ),
    }

    def role_permissions(self, roles: list[str]) -> frozenset[str]:
        """Expand a list of roles into the set of granted permissions.

        Args:
            roles: The roles assigned to the caller.

        Returns:
            The union of permissions granted by those roles.
        """
        granted: set[str] = set()
        for role in roles:
            granted.update(self._ROLE_PERMISSIONS.get(role, frozenset()))
        return frozenset(granted)

    def is_permitted(self, tool: Any, roles: list[str]) -> bool:
        """Return whether a caller with ``roles`` may invoke ``tool``.

        Args:
            tool: The tool to check.
            roles: The caller's roles.

        Returns:
            True if the caller holds the tool's required permission.
        """
        permissions = self.role_permissions(roles)
        if "*" in permissions:
            return True
        return tool_permission(tool) in permissions

    def requires_approval(self, tool: Any) -> bool:
        """Return whether invoking ``tool`` requires prior human approval.

        Args:
            tool: The tool to check.

        Returns:
            True for ACTION and DESTRUCTIVE risk tiers.
        """
        return tool_risk(tool) in (RiskTier.ACTION, RiskTier.DESTRUCTIVE)


__all__ = ["GovernancePolicy", "GovernedTool", "tool_permission", "tool_risk"]
