"""Workspace session manager — workspace lifecycle, resource scoping, persistence, sharing."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class WorkspaceStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Workspace:
    def __init__(
        self,
        workspace_id: str,
        name: str,
        owner_id: str,
        resource_ids: tuple[str, ...] = (),
        shared_with: tuple[str, ...] = (),
    ) -> None:
        self.workspace_id = workspace_id
        self.name = name
        self.owner_id = owner_id
        self.resource_ids = list(resource_ids)
        self.shared_with = list(shared_with)
        self.status = WorkspaceStatus.ACTIVE
        self.created_at = utc_now()
        self.updated_at = utc_now()
        self.metadata: dict[str, Any] = {}


class WorkspaceManager:
    def __init__(self, event_bus: Any = None) -> None:
        self._workspaces: dict[str, Workspace] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.session.workspace")

    def create_workspace(self, workspace_id: str, name: str, owner_id: str) -> Workspace:
        ws = Workspace(workspace_id=workspace_id, name=name, owner_id=owner_id)
        self._workspaces[workspace_id] = ws
        self._log.info("workspace.created", workspace_id=workspace_id, owner=owner_id)
        return ws

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        return self._workspaces.get(workspace_id)

    def list_workspaces(self, owner_id: str | None = None) -> list[Workspace]:
        results = list(self._workspaces.values())
        if owner_id:
            results = [w for w in results if w.owner_id == owner_id]
        return results

    def update_workspace(self, workspace_id: str, name: str | None = None) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            return False
        if name is not None:
            ws.name = name
        ws.updated_at = utc_now()
        return True

    def archive_workspace(self, workspace_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            return False
        ws.status = WorkspaceStatus.ARCHIVED
        ws.updated_at = utc_now()
        return True

    def add_resource(self, workspace_id: str, resource_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            return False
        if resource_id not in ws.resource_ids:
            ws.resource_ids.append(resource_id)
            ws.updated_at = utc_now()
        return True

    def remove_resource(self, workspace_id: str, resource_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None or resource_id not in ws.resource_ids:
            return False
        ws.resource_ids.remove(resource_id)
        ws.updated_at = utc_now()
        return True

    def share_workspace(self, workspace_id: str, user_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            return False
        if user_id not in ws.shared_with:
            ws.shared_with.append(user_id)
            ws.updated_at = utc_now()
        return True

    def unshare_workspace(self, workspace_id: str, user_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws is None or user_id not in ws.shared_with:
            return False
        ws.shared_with.remove(user_id)
        ws.updated_at = utc_now()
        return True

    def get_shared_workspaces(self, user_id: str) -> list[Workspace]:
        return [w for w in self._workspaces.values() if user_id in w.shared_with]


__all__ = [
    "Workspace",
    "WorkspaceManager",
    "WorkspaceStatus",
]
