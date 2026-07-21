"""Tests for :mod:`eaip.agentperf.exceptions`."""

from __future__ import annotations

from eaip.agentperf.exceptions import AgentNotFoundError, AnalyzerError
from eaip.exceptions.base import ErrorCode


class TestAnalyzerError:
    def test_base_exception(self) -> None:
        err = AnalyzerError("analyzer failed")
        assert str(err) == "analyzer failed"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestAgentNotFoundError:
    def test_default_code(self) -> None:
        err = AgentNotFoundError("agent not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = AgentNotFoundError("not found")
        assert isinstance(err, AnalyzerError)
