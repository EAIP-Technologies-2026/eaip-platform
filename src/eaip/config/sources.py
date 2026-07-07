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
        """Initialize DictSource with configuration data.

        Args:
            data: The initial dictionary-based configuration.
        """
        self._data = dict(data)

    def load(self) -> Mapping[str, Any]:
        """Return the configuration snapshot.

        Returns:
            The configuration mapping.
        """
        return dict(self._data)


class EnvSource(ConfigSource):
    """Reads ``PREFIX_*`` environment variables and converts to lowercase keys.

    Nested keys use ``__`` as a delimiter (e.g. ``EAIP_LOGGING__LEVEL`` →
    ``{"logging": {"level": "..."}}``).
    """

    __slots__ = ("_environ", "_prefix")

    def __init__(self, *, prefix: str = "EAIP_", environ: Mapping[str, str] | None = None) -> None:
        """Initialize EnvSource.

        Args:
            prefix: The environment variable prefix to match.
            environ: Optional environment mapping; defaults to ``os.environ``.

        Raises:
            ConfigurationError: If prefix is empty or does not end with ``_``.
        """
        if not prefix or not prefix.endswith("_"):
            raise ConfigurationError(
                "EnvSource prefix must be non-empty and end with '_'",
                context={"prefix": prefix},
            )
        self._prefix = prefix
        self._environ = environ if environ is not None else os.environ

    def load(self) -> Mapping[str, Any]:
        """Load configuration from environment variables.

        Returns:
            The loaded configuration mapping.
        """
        result: dict[str, Any] = {}
        for raw_key, raw_value in self._environ.items():
            if not raw_key.startswith(self._prefix):
                continue
            path = raw_key[len(self._prefix) :].lower().split("__")
            self._assign(result, path, raw_value)
        return result

    @staticmethod
    def _assign(target: dict[str, Any], path: list[str], value: str) -> None:
        """Assign a value to the nested target dictionary.

        Args:
            target: The dictionary to update.
            path: The path of keys to traverse.
            value: The value to assign.
        """
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
        """Initialize FileSource.

        Args:
            path: Path to the configuration file.
            required: Whether the file is required.
        """
        self._path = Path(path)
        self._required = required

    def load(self) -> Mapping[str, Any]:
        """Load configuration from a file.

        Returns:
            The loaded configuration mapping.

        Raises:
            ConfigurationError: If the file is not found (and required) or fails to parse.
        """
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
        """Initialize LayeredSource with multiple sources.

        Args:
            *sources: The configuration sources to layer.

        Raises:
            ConfigurationError: If no sources are provided.
        """
        if not sources:
            raise ConfigurationError("LayeredSource requires at least one source")
        self._sources = sources

    def load(self) -> Mapping[str, Any]:
        """Load configuration from all layered sources.

        Returns:
            The merged configuration mapping.
        """
        result: dict[str, Any] = {}
        for source in self._sources:
            _deep_merge(result, dict(source.load()))
        return result


def _deep_merge(dest: dict[str, Any], src: Mapping[str, Any]) -> None:
    """Deep merge source mapping into destination dictionary.

    Args:
        dest: The destination dictionary to update.
        src: The source mapping to merge.
    """
    for key, value in src.items():
        if isinstance(value, Mapping) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


__all__ = ["ConfigSource", "DictSource", "EnvSource", "FileSource", "LayeredSource"]
