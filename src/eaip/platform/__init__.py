"""The top-level :class:`Platform` facade — composes every Foundation layer."""

from __future__ import annotations

from eaip.platform.builder import PlatformBuilder
from eaip.platform.platform import Platform

__all__ = ["Platform", "PlatformBuilder"]
