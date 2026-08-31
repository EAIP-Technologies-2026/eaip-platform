"""Tests for :mod:`eaip.gitsvc.events`."""

from __future__ import annotations

import pytest

from eaip.gitsvc.events import (
    BranchUpdated,
    CommitIndexed,
    RepositoryRegistered,
    WebhookReceived,
)


class TestRepositoryRegistered:
    def test_create(self) -> None:
        e = RepositoryRegistered(
            repo_id="r1", name="repo", url="https://github.com/org/repo", provider="github"
        )
        assert e.event_type == "eaip.gitsvc.repository.registered"

    def test_frozen(self) -> None:
        e = RepositoryRegistered(repo_id="r1", name="n", url="u", provider="gh")
        with pytest.raises(ValueError):
            e.repo_id = "r2"


class TestCommitIndexed:
    def test_create(self) -> None:
        e = CommitIndexed(repo_id="r1", sha="abc", author="dev", files_changed=5)
        assert e.event_type == "eaip.gitsvc.commit.indexed"


class TestWebhookReceived:
    def test_create(self) -> None:
        e = WebhookReceived(repo_id="r1", payload={"ref": "main"})
        assert e.event_type == "eaip.gitsvc.webhook.received"
        assert e.payload["ref"] == "main"


class TestBranchUpdated:
    def test_create(self) -> None:
        e = BranchUpdated(
            repo_id="r1",
            branch="main",
            old_sha="aaa",
            new_sha="bbb",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert e.event_type == "eaip.gitsvc.branch.updated"


def test_all_events_have_unique_types() -> None:
    types = [
        RepositoryRegistered(repo_id="r", name="n", url="u", provider="gh").event_type,
        CommitIndexed(repo_id="r", sha="s", author="a", files_changed=0).event_type,
        WebhookReceived(repo_id="r").event_type,
        BranchUpdated(
            repo_id="r", branch="m", old_sha="o", new_sha="n", timestamp="2025-01-01T00:00:00Z"
        ).event_type,
    ]
    assert len(types) == len(set(types))
