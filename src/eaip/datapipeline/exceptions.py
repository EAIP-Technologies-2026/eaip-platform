from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class PipelineError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class SourceNotFoundError(PipelineError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SinkNotFoundError(PipelineError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class PipelineNotFoundError(PipelineError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class PipelineExecutionError(PipelineError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class StepExecutionError(PipelineError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class DataValidationError(PipelineError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "DataValidationError",
    "PipelineError",
    "PipelineExecutionError",
    "PipelineNotFoundError",
    "SinkNotFoundError",
    "SourceNotFoundError",
    "StepExecutionError",
]
