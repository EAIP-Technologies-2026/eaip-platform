"""Health-check protocol — see :mod:`eaip.health` for the framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from eaip.health.checks import HealthReport


@runtime_checkable
class Healthcheckable(Protocol):
    """A component that can report its own health on demand."""

    async def check_health(self) -> HealthReport: ...


__all__ = ["Healthcheckable"]
