"""Tests for :mod:`eaip.rollbackmgr.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.rollbackmgr.exceptions import DeploymentNotFoundError, RollbackError


class TestRollbackError:
    def test_base_exception(self) -> None:
        err = RollbackError("rollback error")
        assert str(err) == "rollback error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestDeploymentNotFoundError:
    def test_default_code(self) -> None:
        err = DeploymentNotFoundError("deployment not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = DeploymentNotFoundError("not found")
        assert isinstance(err, RollbackError)
