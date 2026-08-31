"""Exception hierarchy for the pipeline orchestration engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class OrchestratorError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class PipelineNotFoundError(OrchestratorError):
    default_code = ErrorCode.NOT_FOUND


class StageExecutionError(OrchestratorError):
    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "OrchestratorError",
    "PipelineNotFoundError",
    "StageExecutionError",
]
