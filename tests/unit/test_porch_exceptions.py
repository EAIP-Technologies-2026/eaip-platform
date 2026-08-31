"""Tests for porch exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.porch.exceptions import (
    OrchestratorError,
    PipelineNotFoundError,
    StageExecutionError,
)


class TestOrchestratorError:
    def test_base_exception(self) -> None:
        err = OrchestratorError("Orchestrator error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestPipelineNotFoundError:
    def test_default_code(self) -> None:
        err = PipelineNotFoundError("Not found")
        assert isinstance(err, OrchestratorError)
        assert err.code == ErrorCode.NOT_FOUND


class TestStageExecutionError:
    def test_default_code(self) -> None:
        err = StageExecutionError("Stage failed")
        assert isinstance(err, OrchestratorError)
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_custom_message(self) -> None:
        err = StageExecutionError("Stage 'st1' execution failed")
        assert "st1" in str(err)
