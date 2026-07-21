"""Migration engine — register, run, rollback, and verify migrations."""

from __future__ import annotations

import asyncio
from hashlib import sha256
from typing import Any

from eaip.datamigrate.events import (
    BatchCompleted,
    BatchFailed,
    BatchStarted,
    MigrationCompleted,
    MigrationFailed,
    MigrationRolledBack,
    MigrationStarted,
    MigrationVerified,
)
from eaip.datamigrate.exceptions import (
    MigrationError,
    MigrationFailedError,
    MigrationNotFoundError,
    RollbackFailedError,
)
from eaip.datamigrate.models import (
    BatchStatus,
    Migration,
    MigrationBatch,
    MigrationStatus,
    MigrationStep,
    MigrationType,
    StepDirection,
    StepStatus,
)
from eaip.shared.time import utc_now


class MigrationEngine:
    def __init__(self) -> None:
        self._migrations: dict[str, Migration] = {}
        self._steps: dict[str, list[MigrationStep]] = {}
        self._batches: dict[str, MigrationBatch] = {}
        self._handlers: dict[str, Any] = {}

    def register_migration(
        self,
        migration_id: str,
        name: str,
        version: str,
        description: str,
        migration_type: MigrationType = MigrationType.DATA,
        steps: list[MigrationStep] | None = None,
        handler: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Migration:
        checksum = sha256(f"{migration_id}:{version}:{description}".encode()).hexdigest()

        migration = Migration(
            id=migration_id,
            name=name,
            version=version,
            description=description,
            type=migration_type,
            checksum=checksum,
            metadata=metadata or {},
        )
        self._migrations[migration_id] = migration
        self._steps[migration_id] = steps or []
        if handler is not None:
            self._handlers[migration_id] = handler
        return migration

    async def run_migration(self, migration_id: str) -> Migration:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise MigrationNotFoundError(
                f"Migration '{migration_id}' not found",
                context={"migration_id": migration_id},
            )

        started = utc_now()

        migration = migration.model_copy(
            update={
                "status": MigrationStatus.RUNNING,
                "started_at": started,
            }
        )
        self._migrations[migration_id] = migration

        MigrationStarted(
            migration_id=migration_id,
            migration_name=migration.name,
            version=migration.version,
            migration_type=migration.type.value,
        )

        try:
            handler = self._handlers.get(migration_id)
            if handler is not None:
                if asyncio.iscoroutinefunction(handler):
                    await handler(migration)
                else:
                    handler(migration)

            for step in self._steps.get(migration_id, []):
                if step.type != StepDirection.UP:
                    continue
                step = step.model_copy(update={"status": StepStatus.RUNNING})
                step_started = utc_now()
                try:
                    handler = self._handlers.get(f"{migration_id}:step:{step.id}")
                    if handler is not None:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(step)
                        else:
                            handler(step)
                    step_duration = (utc_now() - step_started).total_seconds() * 1000
                    step = step.model_copy(
                        update={
                            "status": StepStatus.COMPLETED,
                            "duration_ms": step_duration,
                        }
                    )
                except Exception as exc:
                    step_duration = (utc_now() - step_started).total_seconds() * 1000
                    step = step.model_copy(
                        update={
                            "status": StepStatus.FAILED,
                            "duration_ms": step_duration,
                            "error": str(exc),
                        }
                    )
                    raise

            completed = utc_now()
            duration = (completed - started).total_seconds() * 1000
            migration = migration.model_copy(
                update={
                    "status": MigrationStatus.COMPLETED,
                    "completed_at": completed,
                    "duration_ms": duration,
                }
            )
            self._migrations[migration_id] = migration

            MigrationCompleted(
                migration_id=migration_id,
                migration_name=migration.name,
                duration_ms=duration,
            )

            return migration

        except Exception as exc:
            failed_at = utc_now()
            duration = (failed_at - started).total_seconds() * 1000
            migration = migration.model_copy(
                update={
                    "status": MigrationStatus.FAILED,
                    "completed_at": failed_at,
                    "duration_ms": duration,
                    "error": str(exc),
                }
            )
            self._migrations[migration_id] = migration

            MigrationFailed(
                migration_id=migration_id,
                migration_name=migration.name,
                error=str(exc),
                duration_ms=duration,
            )

            if isinstance(exc, MigrationError):
                raise
            raise MigrationFailedError(
                f"Migration '{migration_id}' failed: {exc}",
                context={"migration_id": migration_id},
                cause=exc,
            ) from exc

    async def run_batch(self, batch_id: str) -> MigrationBatch:
        batch = self._batches.get(batch_id)
        if batch is None:
            raise MigrationNotFoundError(
                f"Batch '{batch_id}' not found",
                context={"batch_id": batch_id},
            )

        started = utc_now()
        batch = batch.model_copy(
            update={
                "status": BatchStatus.RUNNING,
                "started_at": started,
            }
        )
        self._batches[batch_id] = batch

        BatchStarted(
            batch_id=batch_id,
            batch_name=batch.name,
            migration_count=len(batch.migrations),
        )

        try:
            for mid in batch.migrations:
                await self.run_migration(mid)

            completed = utc_now()
            batch = batch.model_copy(
                update={
                    "status": BatchStatus.COMPLETED,
                    "completed_at": completed,
                }
            )
            self._batches[batch_id] = batch

            BatchCompleted(
                batch_id=batch_id,
                batch_name=batch.name,
                migration_count=len(batch.migrations),
            )

            return batch

        except Exception as exc:
            batch = batch.model_copy(
                update={
                    "status": BatchStatus.FAILED,
                    "completed_at": utc_now(),
                }
            )
            self._batches[batch_id] = batch

            BatchFailed(
                batch_id=batch_id,
                batch_name=batch.name,
                error=str(exc),
            )

            if isinstance(exc, MigrationError):
                raise
            raise MigrationFailedError(
                f"Batch '{batch_id}' failed: {exc}",
                context={"batch_id": batch_id},
                cause=exc,
            ) from exc

    async def rollback_migration(self, migration_id: str) -> Migration:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise MigrationNotFoundError(
                f"Migration '{migration_id}' not found",
                context={"migration_id": migration_id},
            )

        if migration.status not in (
            MigrationStatus.COMPLETED,
            MigrationStatus.FAILED,
        ):
            raise RollbackFailedError(
                f"Cannot rollback migration '{migration_id}' with status {migration.status}",
                context={"migration_id": migration_id, "current_status": migration.status.value},
            )

        started = utc_now()

        try:
            steps = self._steps.get(migration_id, [])
            for step in reversed(steps):
                if step.type != StepDirection.ROLLBACK:
                    continue
                step = step.model_copy(update={"status": StepStatus.RUNNING})
                step_started = utc_now()
                handler = self._handlers.get(f"{migration_id}:step:{step.id}")
                if handler is not None:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(step)
                    else:
                        handler(step)
                step_duration = (utc_now() - step_started).total_seconds() * 1000
                step = step.model_copy(
                    update={
                        "status": StepStatus.COMPLETED,
                        "duration_ms": step_duration,
                    }
                )

            completed = utc_now()
            duration = (completed - started).total_seconds() * 1000
            migration = migration.model_copy(
                update={
                    "status": MigrationStatus.ROLLED_BACK,
                    "completed_at": completed,
                    "duration_ms": duration,
                }
            )
            self._migrations[migration_id] = migration

            MigrationRolledBack(
                migration_id=migration_id,
                migration_name=migration.name,
                duration_ms=duration,
            )

            return migration

        except Exception as exc:
            duration = (utc_now() - started).total_seconds() * 1000
            migration = migration.model_copy(
                update={
                    "duration_ms": duration,
                    "error": str(exc),
                }
            )
            self._migrations[migration_id] = migration
            raise RollbackFailedError(
                f"Rollback of '{migration_id}' failed: {exc}",
                context={"migration_id": migration_id},
                cause=exc,
            ) from exc

    async def get_migration(self, migration_id: str) -> Migration:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise MigrationNotFoundError(
                f"Migration '{migration_id}' not found",
                context={"migration_id": migration_id},
            )
        return migration

    async def list_migrations(
        self, status: MigrationStatus | None = None, limit: int = 100
    ) -> list[Migration]:
        result = list(self._migrations.values())
        if status is not None:
            result = [m for m in result if m.status == status]
        return result[:limit]

    async def verify_migration(self, migration_id: str) -> bool:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise MigrationNotFoundError(
                f"Migration '{migration_id}' not found",
                context={"migration_id": migration_id},
            )

        valid = migration.status == MigrationStatus.COMPLETED

        try:
            steps = self._steps.get(migration_id, [])
            for step in steps:
                if step.type != StepDirection.VERIFY:
                    continue
                handler = self._handlers.get(f"{migration_id}:step:{step.id}")
                if handler is not None:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(step)
                    else:
                        result = handler(step)
                    if not result:
                        valid = False
        except Exception:
            valid = False

        MigrationVerified(
            migration_id=migration_id,
            migration_name=migration.name,
            valid=valid,
        )

        return valid
