from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m007_scheduling")


async def up(conn) -> None:
    log.info("Running migration m007_scheduling: up")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id              VARCHAR(36)    NOT NULL,
            tenant_id       VARCHAR(36)    NOT NULL,
            name            VARCHAR(255)   NOT NULL,
            description     TEXT           NOT NULL DEFAULT '',
            target_type     VARCHAR(50)    NOT NULL,
            target_id       VARCHAR(255)   NOT NULL,
            trigger_config  JSONB          NOT NULL DEFAULT '{}'::jsonb,
            window_config   JSONB,
            priority        INT            NOT NULL DEFAULT 1,
            dependencies    TEXT[]         NOT NULL DEFAULT '{}',
            retry_policy    JSONB          NOT NULL DEFAULT '{}'::jsonb,
            status          VARCHAR(50)    NOT NULL DEFAULT 'active',
            created_by      VARCHAR(255)   NOT NULL DEFAULT '',
            created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            next_run_at     TIMESTAMPTZ,
            last_run_at     TIMESTAMPTZ,
            metadata        JSONB          NOT NULL DEFAULT '{}'::jsonb,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedules_tenant ON schedules(tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(tenant_id, status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at) WHERE status = 'active'")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedules_target ON schedules(tenant_id, target_type, target_id)")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schedule_executions (
            id              VARCHAR(36)    PRIMARY KEY,
            schedule_id     VARCHAR(36)    NOT NULL,
            tenant_id       VARCHAR(36)    NOT NULL,
            status          VARCHAR(50)    NOT NULL DEFAULT 'pending',
            attempt         INT            NOT NULL DEFAULT 1,
            scheduled_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            started_at      TIMESTAMPTZ,
            completed_at    TIMESTAMPTZ,
            result          TEXT           NOT NULL DEFAULT '',
            error           TEXT
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedule_executions_tenant ON schedule_executions(tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedule_executions_schedule ON schedule_executions(schedule_id, tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_schedule_executions_status ON schedule_executions(status)")


async def down(conn) -> None:
    log.info("Running migration m007_scheduling: down")
    await conn.execute("DROP TABLE IF EXISTS schedule_executions")
    await conn.execute("DROP TABLE IF EXISTS schedules")


migration = Migration(
    id="m007_scheduling",
    description="Advanced Scheduling backend: schedules and schedule_executions",
    up=up,
    down=down,
)
