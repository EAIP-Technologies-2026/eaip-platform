"""Dead-letter queue — durable capture of failed event handler invocations.

BATCH 01 (Point 03) requires that events which fail subscriber delivery are not
silently dropped.  ``DeadLetterQueue`` persists the original event payload, the
failed handler, and the failure reason to the ``dead_letters`` PostgreSQL table
via the shared :class:`~eaip.infrastructure.db.connection.DatabaseConnection`
pool, and supports retry / purge workflows.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from eaip.events.errors import EventError
from eaip.events.event import DomainEvent
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

log = get_logger("eaip.events.deadletter")

RetryHandler = Callable[[dict[str, Any]], Awaitable[None]]


class DeadLetterError(EventError):
    """Raised when a dead-letter operation cannot be fulfilled."""


class DeadLetterQueue:
    """PostgreSQL-backed dead-letter queue."""

    def _require_db(self) -> None:
        if DatabaseConnection.get_pool() is None:
            raise DeadLetterError(
                "DeadLetterQueue requires an initialized DatabaseConnection pool."
            )

    async def record(
        self,
        event: DomainEvent,
        handler_name: str,
        error: BaseException,
        *,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> str:
        """Persist a failed event delivery as a dead letter.

        Returns the dead-letter id.
        """
        self._require_db()
        letter_id = f"dl-{event.id}"
        await DatabaseConnection.execute(
            """
            INSERT INTO dead_letters
                (id, event_id, event_type, tenant_id, payload, handler_name,
                 error_message, error_traceback, retry_count, max_retries)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
            ON CONFLICT (id) DO UPDATE SET
                handler_name = EXCLUDED.handler_name,
                error_message = EXCLUDED.error_message,
                error_traceback = EXCLUDED.error_traceback,
                retry_count = EXCLUDED.retry_count,
                resolved = FALSE
            """,
            letter_id,
            event.id,
            type(event).__name__,
            event.tenant_id,
            event.model_dump_json(),
            handler_name,
            str(error),
            _traceback(error),
            retry_count,
            max_retries,
        )
        log.warning(
            "deadletter.recorded",
            letter_id=letter_id,
            event_id=event.id,
            handler=handler_name,
            tenant_id=event.tenant_id,
        )
        return letter_id

    async def get(self, letter_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, event_id, event_type, tenant_id, payload, handler_name,
                   error_message, error_traceback, retry_count, max_retries,
                   resolved, created_at, last_retry_at
            FROM dead_letters WHERE id = $1
            """,
            letter_id,
        )
        return _row_to_dict(row) if row else None

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, event_id, event_type, tenant_id, payload, handler_name,
                   error_message, error_traceback, retry_count, max_retries,
                   resolved, created_at, last_retry_at
            FROM dead_letters
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return [_row_to_dict(row) for row in rows]

    async def unresolved(self, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, event_id, event_type, tenant_id, payload, handler_name,
                   error_message, error_traceback, retry_count, max_retries,
                   resolved, created_at, last_retry_at
            FROM dead_letters
            WHERE resolved = FALSE
            ORDER BY created_at ASC
            LIMIT $1
            """,
            limit,
        )
        return [_row_to_dict(row) for row in rows]

    async def retry(self, letter_id: str, handler: RetryHandler) -> bool:
        """Re-invoke ``handler`` for the stored event payload.

        On success the dead letter is marked resolved; on failure the retry
        counter is incremented and ``last_retry_at`` updated.  Returns ``True``
        when the letter was resolved.
        """
        self._require_db()
        letter = await self.get(letter_id)
        if letter is None:
            raise DeadLetterError(f"Dead letter {letter_id!r} not found")
        if letter["resolved"]:
            return True

        payload: dict[str, Any] = {}
        if letter["payload"]:
            try:
                payload = (
                    json.loads(letter["payload"])
                    if isinstance(letter["payload"], str)
                    else letter["payload"]
                )
            except (json.JSONDecodeError, TypeError):
                payload = {}

        retry_count = int(letter["retry_count"] or 0)
        try:
            await handler(payload)
        except BaseException as exc:  # noqa: BLE001
            retry_count += 1
            await DatabaseConnection.execute(
                """
                UPDATE dead_letters
                SET retry_count = $2, last_retry_at = NOW(),
                    error_message = $3, error_traceback = $4
                WHERE id = $1
                """,
                letter_id,
                retry_count,
                str(exc),
                _traceback(exc),
            )
            log.warning(
                "deadletter.retry_failed",
                letter_id=letter_id,
                retry_count=retry_count,
                error=str(exc),
            )
            return False

        await DatabaseConnection.execute(
            """
            UPDATE dead_letters
            SET resolved = TRUE, last_retry_at = NOW(), retry_count = $2
            WHERE id = $1
            """,
            letter_id,
            retry_count + 1,
        )
        log.info("deadletter.resolved", letter_id=letter_id)
        return True

    async def purge(self, older_than: datetime) -> int:
        """Delete dead letters created before ``older_than``."""
        self._require_db()
        result = await DatabaseConnection.execute(
            "DELETE FROM dead_letters WHERE created_at < $1", older_than
        )
        count = int(result.split()[-1]) if result else 0
        log.info("deadletter.purged", count=count)
        return count

    async def purge_older_than_days(self, days: int) -> int:
        return await self.purge(utc_now() - timedelta(days=days))

    async def count(self, *, unresolved_only: bool = False) -> int:
        self._require_db()
        if unresolved_only:
            return await DatabaseConnection.fetchval(
                "SELECT COUNT(*) FROM dead_letters WHERE resolved = FALSE"
            )
        return await DatabaseConnection.fetchval("SELECT COUNT(*) FROM dead_letters")


def _traceback(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "event_type": row["event_type"],
        "tenant_id": row["tenant_id"],
        "payload": row["payload"],
        "handler_name": row["handler_name"],
        "error_message": row["error_message"],
        "error_traceback": row["error_traceback"],
        "retry_count": row["retry_count"],
        "max_retries": row["max_retries"],
        "resolved": row["resolved"],
        "created_at": row["created_at"],
        "last_retry_at": row["last_retry_at"],
    }


__all__ = ["DeadLetterError", "DeadLetterQueue", "RetryHandler"]