"""Tests for :mod:`eaip.logging`."""

from __future__ import annotations

import json
import logging

import structlog

from eaip.logging import (
    LoggingConfig,
    bind_context,
    clear_context,
    configure_logging,
    current_context,
    get_logger,
)
from eaip.logging.context import scoped_context


def test_logger_is_bound(capsys: object) -> None:
    configure_logging(LoggingConfig(level="INFO", format="json"))
    log = get_logger("eaip.test")
    log.info("hello", k="v")
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    payload = json.loads(out.splitlines()[-1])
    assert payload["event"] == "hello"
    assert payload["k"] == "v"
    assert payload["level"] == "info"


def test_redaction(capsys: object) -> None:
    configure_logging(LoggingConfig(level="INFO", format="json"))
    log = get_logger("eaip.test")
    log.info("login", password="s3cret", username="ada")
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    payload = json.loads(out.splitlines()[-1])
    assert payload["password"] == "***REDACTED***"
    assert payload["username"] == "ada"


def test_context_propagates(capsys: object) -> None:
    configure_logging(LoggingConfig(level="INFO", format="json"))
    log = get_logger("eaip.test")
    bind_context(request_id="abc")
    try:
        assert current_context()["request_id"] == "abc"
        log.info("event")
        out = capsys.readouterr().out  # type: ignore[attr-defined]
        payload = json.loads(out.splitlines()[-1])
        assert payload["request_id"] == "abc"
    finally:
        clear_context()


def test_scoped_context_restores() -> None:
    configure_logging()
    bind_context(outer="o")
    try:
        with scoped_context(inner="i"):
            assert current_context() == {"outer": "o", "inner": "i"}
        assert current_context() == {"outer": "o"}
    finally:
        clear_context()


def test_console_format_is_string(capsys: object) -> None:
    configure_logging(LoggingConfig(level="DEBUG", format="console"))
    log = get_logger("eaip.test")
    log.debug("event", k="v")
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "event" in out
