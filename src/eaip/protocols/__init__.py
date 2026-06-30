"""Structural protocols defining capabilities components may opt into.

A ``Protocol`` describes *shape* rather than *inheritance*: any class that
implements the named methods satisfies the contract without an explicit
``isinstance`` relationship. This is the preferred mechanism for shared,
cross-cutting capabilities (``Startable``, ``Healthcheckable``, …) because
it avoids forcing diamond-shaped base classes onto adapters.
"""

from __future__ import annotations

from eaip.protocols.health import Healthcheckable
from eaip.protocols.identifiable import Identifiable, Named, Versioned
from eaip.protocols.lifecycle import (
    AsyncDisposable,
    AsyncStartable,
    AsyncStoppable,
    Disposable,
    Startable,
    Stoppable,
)

__all__ = [
    "AsyncDisposable",
    "AsyncStartable",
    "AsyncStoppable",
    "Disposable",
    "Healthcheckable",
    "Identifiable",
    "Named",
    "Startable",
    "Stoppable",
    "Versioned",
]
