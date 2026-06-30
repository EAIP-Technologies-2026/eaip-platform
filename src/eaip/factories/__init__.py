"""Generic factory helpers.

Most factories in the platform are explicit construction functions; this
module exists to provide a uniform, typed *registry-backed* factory pattern
that several other Foundation packages reuse.
"""

from __future__ import annotations

from eaip.factories.factory import Factory

__all__ = ["Factory"]
