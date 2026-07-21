"""Runtime diagnostics — system-wide health, metrics, and performance data.

Aggregates data from multiple platform subsystems into a single
:class:`RuntimeDiagnostics` snapshot for observability tooling.
"""

from __future__ import annotations

import time
from typing import Any

from eaip.shared.time import utc_now


class RuntimeDiagnosticsService:
    """Collects runtime health and performance data from instrumented components.

    Usage::

        diag = RuntimeDiagnosticsService()
        snapshot = await diag.collect()
    """

    def __init__(self) -> None:
        self._started_at = time.monotonic()

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._started_at

    async def collect(self, **components: Any) -> dict[str, Any]:
        """Collect a snapshot from registered components.

        Args:
            **components: Named subsystems that expose ``get_stats()`` or
                similar diagnostic methods.

        Returns:
            A structured dict with timestamps and component data.
        """
        snapshot: dict[str, Any] = {
            "timestamp": utc_now().isoformat(),
            "uptime_seconds": self.uptime_seconds,
        }
        for name, component in components.items():
            if component is None:
                continue
            try:
                if hasattr(component, "get_stats"):
                    snapshot[name] = await component.get_stats() if hasattr(component, "__aenter__") else component.get_stats()
                elif hasattr(component, "get_snapshot"):
                    snapshot[name] = component.get_snapshot()
                elif hasattr(component, "active_count"):
                    snapshot[name] = {
                        "active_count": component.active_count,
                        "total_count": getattr(component, "total_count", 0),
                    }
                elif hasattr(component, "size"):
                    snapshot[name] = {"size": component.size}
                else:
                    snapshot[name] = {"available": True}
            except Exception as exc:
                snapshot[name] = {"error": str(exc)}
        return snapshot


__all__ = ["RuntimeDiagnosticsService"]
