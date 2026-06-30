"""Application bootstrap & runner — high-level entry points for hosts."""

from __future__ import annotations

from eaip.application.bootstrap import build_platform
from eaip.application.runner import run_platform

__all__ = ["build_platform", "run_platform"]
