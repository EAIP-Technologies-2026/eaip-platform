"""Logging configuration model and one-shot bootstrap."""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog
from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.filters import redact_processor
from eaip.types import LogLevel

LogFormat = Literal["json", "console"]


class LoggingConfig(BaseModel):
    """Declarative configuration for the platform logger."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: LogLevel = Field(default="INFO")
    format: LogFormat = Field(default="json")
    include_caller: bool = Field(default=False)
    redact_keys: tuple[str, ...] = Field(
        default=(
            "password",
            "passwd",
            "secret",
            "token",
            "api_key",
            "authorization",
            "cookie",
        ),
        description="Keys whose values should be redacted in log records.",
    )


class _State:
    configured: bool = False


_state = _State()


def configure_logging(config: LoggingConfig | None = None) -> None:
    """Configure both ``structlog`` and the stdlib ``logging`` module.

    Safe to call multiple times — subsequent calls reconfigure in place.
    """
    cfg = config or LoggingConfig()

    # ------------------------------------------------------------------
    # Stdlib root logger — structlog wraps it for foreign loggers.
    # ------------------------------------------------------------------
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, cfg.level),
        force=True,
    )

    def add_otel_trace_ids(logger, log_method, event_dict):
        """Inject OTel trace_id and span_id if a span is active."""
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span and span.is_recording():
                ctx = span.get_span_context()
                if ctx.is_valid:
                    event_dict["trace_id"] = format(ctx.trace_id, "032x")
                    event_dict["span_id"] = format(ctx.span_id, "016x")
        except ImportError:
            pass
        return event_dict

    # ------------------------------------------------------------------
    # Shared processors that run on every event.
    # ------------------------------------------------------------------
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_otel_trace_ids,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        redact_processor(cfg.redact_keys),
    ]
    if cfg.include_caller:
        shared_processors.insert(
            0,
            structlog.processors.CallsiteParameterAdder(
                parameters={
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                },
            ),
        )

    renderer: structlog.types.Processor
    if cfg.format == "json":
        renderer = structlog.processors.JSONRenderer(sort_keys=True)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, cfg.level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _state.configured = True


def is_configured() -> bool:
    """Return ``True`` if :func:`configure_logging` has run at least once."""
    return _state.configured


__all__ = ["LogFormat", "LoggingConfig", "configure_logging", "is_configured"]
