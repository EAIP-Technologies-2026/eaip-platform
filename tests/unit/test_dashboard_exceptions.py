"""Tests for dashboard exceptions."""

from __future__ import annotations

from eaip.dashboard.exceptions import DashboardError, DashboardNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestDashboardError:
    def test_base_exception(self) -> None:
        err = DashboardError("Dashboard error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Dashboard error"

    def test_with_context(self) -> None:
        err = DashboardError("Error", context={"dashboard_id": "d1"})
        assert err.context == {"dashboard_id": "d1"}


class TestDashboardNotFoundError:
    def test_default_code(self) -> None:
        err = DashboardNotFoundError("Not found")
        assert isinstance(err, DashboardError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = DashboardNotFoundError("Dashboard 'xyz' not found")
        assert "xyz" in str(err)
