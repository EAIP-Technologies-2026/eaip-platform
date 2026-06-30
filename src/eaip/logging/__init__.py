"""Structured logging facade — `structlog` underneath, opinionated defaults on top."""

from __future__ import annotations

from eaip.logging.config import LoggingConfig, configure_logging
from eaip.logging.context import (
    bind_context,
    clear_context,
    current_context,
    get_logger,
)

__all__ = [
    "LoggingConfig",
    "bind_context",
    "clear_context",
    "configure_logging",
    "current_context",
    "get_logger",
]
