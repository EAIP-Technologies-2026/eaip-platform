"""Runtime module protocol — the plug-in contract for runtime extensions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


@runtime_checkable
class RuntimeModule(Protocol):
    """Protocol for pluggable runtime modules with start/stop lifecycle."""

    name: str

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the module; called during kernel boot."""
        ...

    async def stop(self, kernel: RuntimeKernel) -> None:
        """Stop the module; called during kernel shutdown."""
        ...
