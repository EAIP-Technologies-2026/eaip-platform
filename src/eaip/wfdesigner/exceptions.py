"""Exception hierarchy for the workflow designer."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DesignerError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class BlueprintNotFoundError(DesignerError):
    default_code = ErrorCode.NOT_FOUND

    def __init__(self, blueprint_id: str) -> None:
        self.blueprint_id = blueprint_id
        super().__init__(f"blueprint not found: {blueprint_id!r}")


__all__ = [
    "BlueprintNotFoundError",
    "DesignerError",
]
