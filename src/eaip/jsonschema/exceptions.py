"""Exception hierarchy for the JSON schema service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SchemaServiceError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class SchemaNotFoundError(SchemaServiceError):
    default_code = ErrorCode.NOT_FOUND

    def __init__(self, schema_id: str) -> None:
        self.schema_id = schema_id
        super().__init__(f"schema not found: {schema_id!r}")


__all__ = [
    "SchemaNotFoundError",
    "SchemaServiceError",
]
