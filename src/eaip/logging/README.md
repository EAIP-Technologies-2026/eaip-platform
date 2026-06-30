# `eaip.logging`

Structured logging facade backed by [`structlog`](https://www.structlog.org/).

* **Single configuration entry point** — `configure_logging(LoggingConfig(...))`.
* **Two formats** — `json` (default; production) and `console` (TTY-friendly).
* **Context propagation** — `bind_context(**kv)` / `scoped_context(**kv)` propagate via `contextvars`.
* **Redaction** — sensitive keys (`password`, `secret`, `token`, …) are scrubbed before render.
* **Correlation** — any value bound at the start of a request (trace id, run id, tenant id) flows automatically through nested loggers.

Use `get_logger(__name__)` everywhere; do **not** call `logging.getLogger` directly.
