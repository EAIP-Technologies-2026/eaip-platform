"""Config sources: in-memory, environment, file, layered composition."""

from __future__ import annotations

import json
import os
import tomllib
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from eaip.exceptions.domain import ConfigurationError


class ConfigSource(ABC):
    """Read-only source of configuration key/value pairs."""

    @abstractmethod
    def load(self) -> Mapping[str, Any]:
        """Return the configuration snapshot. Implementations must be idempotent."""


class DictSource(ConfigSource):
    """A literal, in-memory dictionary — useful in tests."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = dict(data)

    def load(self) -> Mapping[str, Any]:
        return dict(self._data)


class EnvSource(ConfigSource):
    """Reads ``PREFIX_*`` environment variables and converts to lowercase keys.

    Nested keys use ``__`` as a delimiter (e.g. ``EAIP_LOGGING__LEVEL`` →
    ``{"logging": {"level": "..."}}``).
    """

    __slots__ = ("_environ", "_prefix")

    def __init__(self, *, prefix: str = "EAIP_", environ: Mapping[str, str] | None = None) -> None:
        if not prefix or not prefix.endswith("_"):
            raise ConfigurationError(
                "EnvSource prefix must be non-empty and end with '_'",
                context={"prefix": prefix},
            )
        self._prefix = prefix
        self._environ = environ if environ is not None else os.environ

    def load(self) -> Mapping[str, Any]:
        result: dict[str, Any] = {}
        for raw_key, raw_value in self._environ.items():
            if not raw_key.startswith(self._prefix):
                continue
            path = raw_key[len(self._prefix) :].lower().split("__")
            self._assign(result, path, raw_value)
        return result

    @staticmethod
    def _assign(target: dict[str, Any], path: list[str], value: str) -> None:
        node = target
        for key in path[:-1]:
            existing = node.get(key)
            if not isinstance(existing, dict):
                existing = {}
                node[key] = existing
            node = existing
        node[path[-1]] = value


class FileSource(ConfigSource):
    """Reads JSON or TOML from a file path. Format is inferred by suffix."""

    __slots__ = ("_path", "_required")

    def __init__(self, path: str | Path, *, required: bool = True) -> None:
        self._path = Path(path)
        self._required = required

    def load(self) -> Mapping[str, Any]:
        if not self._path.exists():
            if self._required:
                raise ConfigurationError(
                    f"required config file not found: {self._path}",
                    context={"path": str(self._path)},
                )
            return {}
        suffix = self._path.suffix.lower()
        try:
            if suffix == ".json":
                return cast(Mapping[str, Any], json.loads(self._path.read_text(encoding="utf-8")))
            if suffix == ".toml":
                with self._path.open("rb") as handle:
                    return tomllib.load(handle)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, OSError) as exc:
            raise ConfigurationError(
                f"failed to parse config file {self._path}: {exc}",
                context={"path": str(self._path)},
                cause=exc,
            ) from exc
        raise ConfigurationError(
            f"unsupported config file format: {suffix}",
            context={"path": str(self._path)},
        )


class LayeredSource(ConfigSource):
    """Merges multiple sources; later sources override earlier ones (deep-merge)."""

    __slots__ = ("_sources",)

    def __init__(self, *sources: ConfigSource) -> None:
        if not sources:
            raise ConfigurationError("LayeredSource requires at least one source")
        self._sources = sources

    def load(self) -> Mapping[str, Any]:
        result: dict[str, Any] = {}
        for source in self._sources:
            _deep_merge(result, dict(source.load()))
        return result


def _deep_merge(dest: dict[str, Any], src: Mapping[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, Mapping) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


__all__ = ["ConfigSource", "DictSource", "EnvSource", "FileSource", "LayeredSource"]
