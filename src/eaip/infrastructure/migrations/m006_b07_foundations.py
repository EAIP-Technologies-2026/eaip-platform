"""Migration 006: B07 - Intelligence Pulse, Decisions, Recommendations."""

from eaip.infrastructure.db import DatabaseConnection
from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m006_b07")

async def up(db: DatabaseConnection) -> None:
    log.info("Running migration m006_b07_foundations: up")
    
    # 1. Pulse Metrics
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS pulse_metrics (
            id VARCHAR(36) PRIMARY KEY,
            tenant_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            value FLOAT NOT NULL,
            dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pulse_metrics_tenant ON pulse_metrics(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_pulse_metrics_name ON pulse_metrics(name);
        """
    )
    
    # 2. Decision Logs
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS decision_logs (
            id VARCHAR(36) PRIMARY KEY,
            tenant_id VARCHAR(36) NOT NULL,
            decision_type VARCHAR(255) NOT NULL,
            context JSONB NOT NULL DEFAULT '{}'::jsonb,
            outcome JSONB NOT NULL DEFAULT '{}'::jsonb,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_decision_logs_tenant ON decision_logs(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_decision_logs_type ON decision_logs(decision_type);
        """
    )
    
    # 3. Recommendations
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            id VARCHAR(36) PRIMARY KEY,
            tenant_id VARCHAR(36) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            score FLOAT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_recommendations_tenant ON recommendations(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);
        """
    )


async def down(db: DatabaseConnection) -> None:
    log.info("Running migration m006_b07_foundations: down")
    await db.execute("DROP TABLE IF EXISTS recommendations;")
    await db.execute("DROP TABLE IF EXISTS decision_logs;")
    await db.execute("DROP TABLE IF EXISTS pulse_metrics;")

migration = Migration(id="m006_b07_foundations", description="B07 - Intelligence Pulse, Decisions, Recommendations", up=up, down=down)
