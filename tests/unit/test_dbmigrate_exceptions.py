"""Tests for :mod:`eaip.dbmigrate.exceptions`."""

from __future__ import annotations

from eaip.dbmigrate.exceptions import DBMigrationError, ScriptNotFoundError
from eaip.exceptions.base import ErrorCode


class TestDBMigrationError:
    def test_base_exception(self) -> None:
        err = DBMigrationError("db migration error")
        assert str(err) == "db migration error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestScriptNotFoundError:
    def test_default_code(self) -> None:
        err = ScriptNotFoundError("script not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = ScriptNotFoundError("not found")
        assert isinstance(err, DBMigrationError)
