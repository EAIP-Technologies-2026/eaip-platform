"""Tests for :mod:`eaip.gitsvc.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.gitsvc.models import (
    GitCommit,
    GitConfig,
    GitRepository,
    GitRepositoryStatus,
    GitWebhookEvent,
)


class TestGitRepository:
    def test_create_minimal(self) -> None:
        r = GitRepository(id="r1", name="my-repo", url="https://github.com/org/repo")
        assert r.status is GitRepositoryStatus.ACTIVE
        assert r.branch == "main"

    def test_frozen(self) -> None:
        r = GitRepository(id="r1", name="n", url="https://github.com/org/repo")
        with pytest.raises(ValidationError):
            r.name = "changed"


class TestGitCommit:
    def test_create(self) -> None:
        c = GitCommit(
            id="c1",
            repo_id="r1",
            sha="abc123",
            author="dev",
            message="fix bug",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert c.files_changed == 0

    def test_frozen(self) -> None:
        c = GitCommit(
            id="c1",
            repo_id="r1",
            sha="abc",
            author="dev",
            message="msg",
            timestamp="2025-01-01T00:00:00Z",
        )
        with pytest.raises(ValidationError):
            c.sha = "def"


class TestGitWebhookEvent:
    def test_create(self) -> None:
        w = GitWebhookEvent(id="w1", repo_id="r1", event_type="push")
        assert w.payload == {}


class TestGitConfig:
    def test_defaults(self) -> None:
        c = GitConfig()
        assert c.default_branch == "main"
        assert c.webhook_retry_limit == 3

    def test_frozen(self) -> None:
        c = GitConfig()
        with pytest.raises(ValidationError):
            c.default_branch = "dev"


class TestGitRepositoryStatus:
    def test_values(self) -> None:
        assert GitRepositoryStatus.ACTIVE.value == "active"
        assert GitRepositoryStatus.INACTIVE.value == "inactive"
        assert GitRepositoryStatus.ERROR.value == "error"


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        GitRepository(id="r1", name="n", url="u", unknown="x")
