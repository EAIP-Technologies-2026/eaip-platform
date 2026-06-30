"""Imperative validation helpers used by services that cannot rely on
Pydantic's declarative parsing (e.g. dynamic config from plugins)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as _PydanticValidationError

from eaip.exceptions.domain import ValidationError

T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)


def ensure(condition: bool, message: str, **context: object) -> None:
    """Raise :class:`ValidationError` if ``condition`` is falsy."""
    if not condition:
        raise ValidationError(message, context=dict(context))


def validate_range(
    value: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    name: str = "value",
) -> float:
    """Validate ``value`` lies within the inclusive ``[minimum, maximum]`` range."""
    if minimum is not None and value < minimum:
        raise ValidationError(
            f"{name} must be ≥ {minimum}; got {value}",
            context={"name": name, "value": value, "minimum": minimum},
        )
    if maximum is not None and value > maximum:
        raise ValidationError(
            f"{name} must be ≤ {maximum}; got {value}",
            context={"name": name, "value": value, "maximum": maximum},
        )
    return value


def validate_one_of(value: T, allowed: Iterable[T], *, name: str = "value") -> T:
    """Validate that ``value`` is one of ``allowed``."""
    allowed_set = list(allowed)
    if value not in allowed_set:
        raise ValidationError(
            f"{name}={value!r} is not one of {allowed_set!r}",
            context={"name": name, "value": value, "allowed": allowed_set},
        )
    return value


def validate_model(model_cls: type[M], data: object) -> M:
    """Validate ``data`` against a Pydantic model, raising :class:`ValidationError`.

    This wrapper translates Pydantic's own ``ValidationError`` into the
    platform's typed equivalent so all callers see a single exception type.
    """
    try:
        return model_cls.model_validate(data)
    except _PydanticValidationError as exc:
        raise ValidationError(
            f"failed to validate {model_cls.__name__}",
            context={"errors": exc.errors(include_url=False)},
            cause=exc,
        ) from exc


__all__ = ["ensure", "validate_model", "validate_one_of", "validate_range"]
