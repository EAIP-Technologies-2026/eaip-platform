"""Tests for :mod:`eaip.validation`."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from eaip.exceptions.domain import ValidationError
from eaip.validation import ensure, validate_model, validate_one_of, validate_range


def test_ensure_passes() -> None:
    ensure(True, "should not raise")


def test_ensure_raises_with_context() -> None:
    with pytest.raises(ValidationError) as exc:
        ensure(False, "nope", x=1)
    assert exc.value.context == {"x": 1}


def test_validate_range() -> None:
    assert validate_range(5, minimum=1, maximum=10) == 5
    with pytest.raises(ValidationError):
        validate_range(0, minimum=1)
    with pytest.raises(ValidationError):
        validate_range(11, maximum=10)


def test_validate_one_of() -> None:
    assert validate_one_of("a", ["a", "b"]) == "a"
    with pytest.raises(ValidationError):
        validate_one_of("z", ["a", "b"], name="colour")


class _M(BaseModel):
    n: int


def test_validate_model_translates_errors() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_model(_M, {"n": "not-an-int"})
    assert exc.value.context.get("errors")
