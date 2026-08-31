# PostgreSQL Persistence

## Overview

EAIP uses PostgreSQL as its primary persistent store. All domain entities are persisted in relational tables with JSONB for flexible metadata fields.

## Architecture

```
AbstractRepository (port/interface)
    ├── InMemoryRepository (dev/test)
    └── PostgresRepository (production)
            └── asyncpg connection pool
```

The `AbstractRepository[ID, T]` interface defines the contract. `PostgresRepository` implements it using asyncpg with connection pooling, prepared statements, and transaction support.

## Connection Management

`DatabaseConnection` is a singleton class managing the asyncpg pool:
- Initialized on platform startup
- Configured via `EAIP_DB__*` environment variables
- Provides `connection()` and `transaction()` context managers
- Health check via `health()` method

## Schema

The initial migration (`001_initial_schema.sql`) creates tables for:
- organizations, users, auth_tokens
- agents, agent_runs
- workflows, workflow_versions, workflow_runs
- missions, mission_executions
- knowledge_collections, knowledge_documents
- deployments, audit_events, runtime_events
- notifications, feature_flags, platform_settings
- memory_metadata

## Migrations

Migrations use a custom `MigrationEngine` that:
- Tracks applied migrations in `_eaip_migrations` table
- Supports up/down migrations
- Runs pending migrations on startup
- Provides rollback capability

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EAIP_DB__HOST` | localhost | PostgreSQL host |
| `EAIP_DB__PORT` | 5432 | PostgreSQL port |
| `EAIP_DB__NAME` | eaip | Database name |
| `EAIP_DB__USER` | eaip | Database user |
| `EAIP_DB__PASSWORD` | eaip_dev_password | Database password |
| `EAIP_DB__MIN_POOL_SIZE` | 2 | Min connection pool size |
| `EAIP_DB__MAX_POOL_SIZE` | 20 | Max connection pool size |
