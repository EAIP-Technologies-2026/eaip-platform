"""High-level helper that hydrates a Pydantic model from one or more sources."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from eaip.config.sources import ConfigSource
from eaip.validation.validators import validate_model

M = TypeVar("M", bound=BaseModel)


class ConfigLoader:
    """Compose :class:`ConfigSource` instances and validate into a typed model."""

    __slots__ = ("_source",)

    def __init__(self, source: ConfigSource) -> None:
        self._source = source

    def load(self, model_cls: type[M]) -> M:
        """Load raw config and validate into ``model_cls``."""
        raw = self._source.load()
        return validate_model(model_cls, raw)


__all__ = ["ConfigLoader"]
