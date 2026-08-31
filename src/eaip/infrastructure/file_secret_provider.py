"""File-based :class:`SecretProviderPort` implementation.

Reads secrets from a JSON or dotenv file.  Useful for local development
and for environments where a vault is not available.

Usage::

    from eaip.infrastructure.file_secret_provider import FileSecretProvider

    provider = FileSecretProvider(path="/etc/eaip/secrets.json")
    secret = provider.get("EAIP_AUTH_SECRET")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eaip.exceptions.domain import NotFoundError


class FileSecretProvider:
    """Resolves secrets from a JSON file on disk.

    Supports JSON files with key-value pairs and .env-style files.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._secrets: dict[str, str] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        path = Path(self._path)
        if not path.exists():
            self._secrets = {}
            self._loaded = True
            return
        content = path.read_text().strip()
        if content.startswith("{"):
            data: dict[str, Any] = json.loads(content)
            self._secrets = {k: str(v) for k, v in data.items()}
        else:
            self._secrets = {}
            for raw_line in content.splitlines():
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                self._secrets[key.strip()] = value.strip().strip('"').strip("'")
        self._loaded = True

    def get(self, name: str) -> str | None:
        if not name:
            raise ValueError("secret name must be non-empty")
        self._load()
        return self._secrets.get(name)

    def require(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise NotFoundError(
                f"required secret {name!r} not found in {self._path}",
                context={"secret": name, "path": self._path},
            )
        return value


__all__ = ["FileSecretProvider"]
