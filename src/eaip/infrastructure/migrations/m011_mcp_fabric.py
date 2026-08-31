from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m011_mcp")


async def up(conn) -> None:
    log.info("Running migration m011_mcp_fabric: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_servers (
                server_id       VARCHAR         NOT NULL,
                tenant_id       VARCHAR         NOT NULL,
                name            VARCHAR         NOT NULL,
                transport_type  VARCHAR         NOT NULL DEFAULT 'stdio',
                endpoint        VARCHAR         NOT NULL DEFAULT '',
                command         VARCHAR         NOT NULL DEFAULT '',
                args            TEXT[]          NOT NULL DEFAULT '{}',
                status          VARCHAR         NOT NULL DEFAULT 'draft',
                capabilities    JSONB           NOT NULL DEFAULT '[]'::jsonb,
                version         VARCHAR         NOT NULL DEFAULT '1.0.0',
                permissions     TEXT[]          NOT NULL DEFAULT '{}',
                created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                last_health_at  TIMESTAMPTZ,
                metadata        JSONB           NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (server_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_servers_tenant ON mcp_servers(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_servers_status ON mcp_servers(tenant_id, status)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_tools (
                name            VARCHAR         NOT NULL,
                server_id       VARCHAR         NOT NULL,
                tenant_id       VARCHAR         NOT NULL,
                description     TEXT            NOT NULL DEFAULT '',
                input_schema    JSONB           NOT NULL DEFAULT '{}'::jsonb,
                permissions     TEXT[]          NOT NULL DEFAULT '{}',
                availability    BOOLEAN         NOT NULL DEFAULT TRUE,
                version         VARCHAR         NOT NULL DEFAULT '1.0.0',
                PRIMARY KEY (name, server_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_tools_tenant ON mcp_tools(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_credentials (
                credential_id   VARCHAR         NOT NULL,
                tenant_id       VARCHAR         NOT NULL,
                credential_type VARCHAR         NOT NULL DEFAULT 'api_key',
                provider        VARCHAR         NOT NULL DEFAULT '',
                reference       TEXT            NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                PRIMARY KEY (credential_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_creds_tenant ON mcp_credentials(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m011_mcp_fabric fallback", error=repr(exc))


async def down(conn) -> None:
    log.info("Running migration m011_mcp_fabric: down")
    try:
        await conn.execute("DROP TABLE IF EXISTS mcp_credentials")
        await conn.execute("DROP TABLE IF EXISTS mcp_tools")
        await conn.execute("DROP TABLE IF EXISTS mcp_servers")
    except Exception as exc:  # pragma: no cover
        log.warning("m011_mcp_fabric down fallback", error=repr(exc))


migration = Migration(id="m011_mcp_fabric", description="MCP connector fabric: mcp_servers, mcp_tools, mcp_credentials with tenant isolation", up=up, down=down)
