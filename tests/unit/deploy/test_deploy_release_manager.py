"""Tests for ReleaseManager."""

from __future__ import annotations

from eaip.deploy.release_manager import ReleaseManager


class TestReleaseManager:
    def test_create_release(self) -> None:
        mgr = ReleaseManager()
        release = mgr.create_release(
            release_id="r1",
            version="1.0.0",
            name="Initial Release",
            description="First release",
        )
        assert release.release_id == "r1"
        assert release.version == "1.0.0"
        assert release.name == "Initial Release"
        assert release.description == "First release"
        assert release.status == "draft"

    def test_get_release_found(self) -> None:
        mgr = ReleaseManager()
        mgr.create_release(release_id="r1", version="1.0", name="R1")
        release = mgr.get_release("r1")
        assert release is not None
        assert release.release_id == "r1"

    def test_get_release_not_found(self) -> None:
        mgr = ReleaseManager()
        release = mgr.get_release("nonexistent")
        assert release is None

    def test_promote_release_valid(self) -> None:
        mgr = ReleaseManager()
        mgr.create_release(release_id="r1", version="1.0", name="R1")
        mgr.update_status("r1", "testing")
        promoted = mgr.promote_release("r1", "staging", "prod")
        assert promoted is not None
        assert promoted.release_id == "r1"

    def test_promote_release_not_found(self) -> None:
        mgr = ReleaseManager()
        promoted = mgr.promote_release("nonexistent", "staging", "prod")
        assert promoted is None

    def test_promote_release_draft_not_promotable(self) -> None:
        mgr = ReleaseManager()
        mgr.create_release(release_id="r1", version="1.0", name="R1")
        promoted = mgr.promote_release("r1", "staging", "prod")
        assert promoted is None

    def test_update_status(self) -> None:
        mgr = ReleaseManager()
        mgr.create_release(release_id="r1", version="1.0", name="R1")
        updated = mgr.update_status("r1", "building")
        assert updated is not None
        assert updated.status == "building"

    def test_update_status_not_found(self) -> None:
        mgr = ReleaseManager()
        updated = mgr.update_status("nonexistent", "building")
        assert updated is None

    def test_releases_property(self) -> None:
        mgr = ReleaseManager()
        mgr.create_release(release_id="r1", version="1.0", name="R1")
        mgr.create_release(release_id="r2", version="2.0", name="R2")
        assert len(mgr.releases) == 2
        assert "r1" in mgr.releases
        assert "r2" in mgr.releases
