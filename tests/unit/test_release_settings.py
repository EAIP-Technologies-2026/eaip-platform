"""Tests for release metadata configuration (:mod:`eaip.settings.core_settings.ReleaseSettings`)."""

from __future__ import annotations

from eaip.settings.core_settings import PlatformSettings, ReleaseSettings, load_platform_settings


class TestReleaseSettingsDefaults:
    def test_defaults_all_none(self) -> None:
        r = ReleaseSettings()
        assert r.version is None
        assert r.environment is None
        assert r.commit is None
        assert r.branch is None
        assert r.deployed_by is None


class TestReleaseSettingsEnvParsing:
    def test_standalone_env_overrides(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_RELEASE_VERSION", "1.2.3")  # type: ignore[attr-defined]
        monkeypatch.setenv("EAIP_RELEASE_COMMIT", "abc123")  # type: ignore[attr-defined]
        monkeypatch.setenv("EAIP_RELEASE_BRANCH", "main")  # type: ignore[attr-defined]
        r = ReleaseSettings()
        assert r.version == "1.2.3"
        assert r.commit == "abc123"
        assert r.branch == "main"


class TestReleaseSettingsOnPlatform:
    def test_platform_defaults(self) -> None:
        s = PlatformSettings()
        assert s.release.version is None

    def test_platform_env_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_RELEASE__VERSION", "0.0.2")  # type: ignore[attr-defined]
        s = load_platform_settings()
        assert s.release.version == "0.0.2"


__all__: list[str] = []
