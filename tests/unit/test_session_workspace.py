from __future__ import annotations

import pytest

from eaip.session.workspace import WorkspaceManager, WorkspaceStatus


class TestWorkspaceManager:
    @pytest.fixture
    def manager(self) -> WorkspaceManager:
        return WorkspaceManager()

    def test_create_workspace(self, manager: WorkspaceManager) -> None:
        ws = manager.create_workspace("w1", "My Workspace", "user1")
        assert ws.workspace_id == "w1"
        assert ws.owner_id == "user1"

    def test_get_workspace(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "test", "user1")
        ws = manager.get_workspace("w1")
        assert ws is not None

    def test_get_nonexistent(self, manager: WorkspaceManager) -> None:
        ws = manager.get_workspace("nonexistent")
        assert ws is None

    def test_list_workspaces(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "a", "user1")
        manager.create_workspace("w2", "b", "user2")
        assert len(manager.list_workspaces()) == 2
        assert len(manager.list_workspaces(owner_id="user1")) == 1

    def test_update_workspace(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "old", "user1")
        result = manager.update_workspace("w1", name="new")
        assert result is True
        ws = manager.get_workspace("w1")
        assert ws is not None
        assert ws.name == "new"

    def test_archive_workspace(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "test", "user1")
        result = manager.archive_workspace("w1")
        assert result is True
        ws = manager.get_workspace("w1")
        assert ws is not None
        assert ws.status == WorkspaceStatus.ARCHIVED

    def test_add_remove_resource(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "test", "user1")
        assert manager.add_resource("w1", "res1") is True
        ws = manager.get_workspace("w1")
        assert ws is not None
        assert "res1" in ws.resource_ids
        assert manager.remove_resource("w1", "res1") is True
        assert "res1" not in ws.resource_ids

    def test_share_unshare(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "test", "user1")
        assert manager.share_workspace("w1", "user2") is True
        ws = manager.get_workspace("w1")
        assert ws is not None
        assert "user2" in ws.shared_with
        assert manager.unshare_workspace("w1", "user2") is True
        assert "user2" not in ws.shared_with

    def test_get_shared_workspaces(self, manager: WorkspaceManager) -> None:
        manager.create_workspace("w1", "a", "user1")
        manager.create_workspace("w2", "b", "user2")
        manager.share_workspace("w1", "user3")
        shared = manager.get_shared_workspaces("user3")
        assert len(shared) == 1

    def test_update_nonexistent(self, manager: WorkspaceManager) -> None:
        assert manager.update_workspace("nonexistent") is False
