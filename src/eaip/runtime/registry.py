"""RuntimeRegistry — central registry for runtime modules and their metadata.

The :class:`RuntimeRegistry` provides a single point of query for all
:class:`~eaip.runtime.module.RuntimeModule` instances registered with the
kernel.  It tracks:

* Which modules are registered.
* Each module's dependency list and health status.
* Aggregate kernel-level metadata.

This is **not** a replacement for :class:`~eaip.runtime.loader.ModuleLoader`
(which handles validation and uniqueness guarantees).  The registry is a
read-biased, query-friendly companion used by diagnostics, tooling, and
external integration points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.runtime.module import RuntimeModule


@dataclass(frozen=True, slots=True)
class ModuleEntry:
    """Immutable snapshot of a runtime module's registration metadata."""

    name: str
    dependencies: tuple[str, ...]
    registered_at: str


class RuntimeRegistry:
    """Central registry of runtime modules and their metadata."""

    def __init__(self) -> None:
        self._entries: dict[str, ModuleEntry] = {}
        self._health_statuses: dict[str, str] = {}

    def register_module(self, module: RuntimeModule) -> None:
        """Record a module in the registry."""
        self._entries[module.name] = ModuleEntry(
            name=module.name,
            dependencies=module.dependencies,
            registered_at=utc_now().isoformat(),
        )

    def unregister_module(self, name: str) -> bool:
        """Remove a module from the registry. Returns ``True`` if it existed."""
        self._health_statuses.pop(name, None)
        return self._entries.pop(name, None) is not None

    def get_entry(self, name: str) -> ModuleEntry | None:
        """Return the :class:`ModuleEntry` for ``name``, or ``None``."""
        return self._entries.get(name)

    def module_names(self) -> list[str]:
        """Sorted list of registered module names."""
        return sorted(self._entries)

    def module_count(self) -> int:
        return len(self._entries)

    def has_module(self, name: str) -> bool:
        return name in self._entries

    def set_health_status(self, module_name: str, status: str) -> None:
        self._health_statuses[module_name] = status

    def get_health_status(self, module_name: str) -> str | None:
        return self._health_statuses.get(module_name)

    def module_metadata(self, name: str) -> dict[str, Any] | None:
        """Return a rich metadata dict for a module, or ``None``."""
        entry = self._entries.get(name)
        if entry is None:
            return None
        return {
            "name": entry.name,
            "dependencies": list(entry.dependencies),
            "registered_at": entry.registered_at,
            "health_status": self._health_statuses.get(name),
        }

    def all_metadata(self) -> dict[str, dict[str, Any]]:
        """Return metadata for every registered module keyed by name."""
        return {
            name: self.module_metadata(name)
            for name in self.module_names()
        }

    def clear(self) -> None:
        self._entries.clear()
        self._health_statuses.clear()


__all__ = ["ModuleEntry", "RuntimeRegistry"]
