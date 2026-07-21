"""Tests for :mod:`eaip.gitsvc.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.gitsvc.exceptions import GitServiceError, RepositoryNotFoundError


class TestGitExceptionHierarchy:
    def test_git_service_error_is_eaip_error(self) -> None:
        assert issubclass(GitServiceError, EAIPError)

    def test_not_found_is_git_service_error(self) -> None:
        assert issubclass(RepositoryNotFoundError, GitServiceError)


class TestErrorCodes:
    def test_git_service_error_code(self) -> None:
        err = GitServiceError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        err = RepositoryNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    def test_message_preserved(self) -> None:
        err = RepositoryNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        err = GitServiceError("bad", context={"repo_id": "r1"})
        assert err.context["repo_id"] == "r1"
