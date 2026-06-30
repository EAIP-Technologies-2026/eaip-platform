"""Tests for :mod:`eaip.config`."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from eaip.config import ConfigLoader, DictSource, EnvSource, FileSource, LayeredSource
from eaip.exceptions.domain import ConfigurationError


class _Inner(BaseModel):
    level: str = "INFO"


class _Cfg(BaseModel):
    name: str
    inner: _Inner = _Inner()


def test_dict_source() -> None:
    cfg = ConfigLoader(DictSource({"name": "x", "inner": {"level": "DEBUG"}})).load(_Cfg)
    assert cfg.name == "x" and cfg.inner.level == "DEBUG"


def test_env_source_nesting() -> None:
    src = EnvSource(
        prefix="X_",
        environ={"X_NAME": "y", "X_INNER__LEVEL": "WARNING", "OTHER": "skip"},
    )
    assert src.load() == {"name": "y", "inner": {"level": "WARNING"}}


def test_env_source_prefix_validation() -> None:
    with pytest.raises(ConfigurationError):
        EnvSource(prefix="BAD")  # missing trailing underscore


def test_file_source_json(tmp_path: Path) -> None:
    p = tmp_path / "c.json"
    p.write_text('{"name": "z"}', encoding="utf-8")
    assert FileSource(p).load() == {"name": "z"}


def test_file_source_toml(tmp_path: Path) -> None:
    p = tmp_path / "c.toml"
    p.write_text('name = "z"\n[inner]\nlevel = "ERROR"\n', encoding="utf-8")
    assert FileSource(p).load() == {"name": "z", "inner": {"level": "ERROR"}}


def test_file_source_missing_required(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        FileSource(tmp_path / "nope.json").load()


def test_file_source_missing_optional(tmp_path: Path) -> None:
    assert FileSource(tmp_path / "nope.json", required=False).load() == {}


def test_layered_deep_merge() -> None:
    s = LayeredSource(
        DictSource({"name": "a", "inner": {"level": "INFO"}}),
        DictSource({"inner": {"level": "DEBUG"}}),
    )
    assert s.load() == {"name": "a", "inner": {"level": "DEBUG"}}
