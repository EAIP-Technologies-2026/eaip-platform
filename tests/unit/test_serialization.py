"""Tests for :mod:`eaip.serialization`."""

from __future__ import annotations

import dataclasses
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import PurePosixPath

import pytest
from pydantic import BaseModel

from eaip.exceptions.domain import SerializationError
from eaip.serialization import from_json, to_json


class Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


@dataclasses.dataclass
class Point:
    x: int
    y: int


class Profile(BaseModel):
    name: str
    age: int


def test_encodes_pydantic_model() -> None:
    out = to_json(Profile(name="ada", age=37))
    assert from_json(out) == {"name": "ada", "age": 37}


def test_encodes_enum_and_dataclass() -> None:
    out = to_json({"c": Colour.RED, "p": Point(1, 2)})
    assert from_json(out) == {"c": "red", "p": {"x": 1, "y": 2}}


def test_encodes_uuid_path_decimal() -> None:
    uid = uuid.uuid4()
    out = to_json(
        {
            "uid": uid,
            "p": PurePosixPath("/var/log"),
            "d": Decimal("1.25"),
            "s": {"a", "b"},
        }
    )
    parsed = from_json(out)
    assert parsed["uid"] == str(uid)
    assert parsed["p"] == "/var/log"
    assert parsed["d"] == "1.25"
    assert parsed["s"] == sorted({"a", "b"})


def test_datetime_is_utc_iso() -> None:
    n = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert from_json(to_json(n)) == n.isoformat()


def test_naive_datetime_is_coerced_to_utc() -> None:
    naive = datetime(2026, 1, 1, 12, 0)
    text = to_json(naive)
    assert text.endswith('+00:00"')


def test_unsupported_type_raises() -> None:
    class _Weird:
        pass

    with pytest.raises(SerializationError):
        to_json(_Weird())


def test_invalid_json_raises_serialization_error() -> None:
    with pytest.raises(SerializationError):
        from_json("not json")


def test_to_json_with_object_dunder() -> None:
    class _CustomJson:
        def __json__(self) -> dict[str, int]:
            return {"v": 5}

    assert from_json(to_json(_CustomJson())) == {"v": 5}
