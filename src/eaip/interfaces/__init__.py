"""Abstract base interfaces enforcing stricter contracts than Protocols.

Use :mod:`eaip.interfaces` (inheritance) when you need:
* default behaviour shared by all implementations;
* a documented, named taxonomy of components;
* explicit ``isinstance`` checks against a stable type.

Use :mod:`eaip.protocols` (structural) when you just need to describe a
shape that arbitrary classes may satisfy.
"""

from __future__ import annotations

from eaip.interfaces.repository import AbstractRepository
from eaip.interfaces.service import AbstractService, ServiceState

__all__ = ["AbstractRepository", "AbstractService", "ServiceState"]
