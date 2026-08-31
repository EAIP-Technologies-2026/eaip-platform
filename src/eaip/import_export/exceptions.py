"""Exception hierarchy for the import/export engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ImportExportError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ImportError(ImportExportError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ExportError(ImportExportError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ImportValidationError(ImportExportError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


class ExportFormatError(ImportExportError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


class ImportMappingError(ImportExportError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


class ExportSchedulingError(ImportExportError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ImportExportConfigError(ImportExportError):
    default_code = ErrorCode.CONFIGURATION_INVALID
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "ExportError",
    "ExportFormatError",
    "ExportSchedulingError",
    "ImportError",
    "ImportExportConfigError",
    "ImportExportError",
    "ImportMappingError",
    "ImportValidationError",
]
