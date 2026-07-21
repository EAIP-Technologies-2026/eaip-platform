# EAIP Backup & Recovery

> **Status:** Alpha → Beta
> **Last updated:** 2026-07-11

---

## Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL database | `pg_dump` | Daily | 30 days |
| Redis data | `SAVE` / RDB snapshots | Hourly | 7 days |
| Qdrant vectors | Collection export | Daily | 30 days |
| Application state | Checkpoint export | On mission completion | Until overwritten |
| Configuration | Git (IaC) | On change | Infinite (git history) |

## PostgreSQL Backup

```bash
# Full backup
pg_dump -h localhost -U eaip -d eaip > eaip-backup-$(date +%Y%m%d).sql

# Restore
psql -h localhost -U eaip -d eaip < eaip-backup-20260711.sql
```

## Restore Procedure

1. Stop the EAIP API: `docker compose stop eaip-api`
2. Restore PostgreSQL from backup
3. Restore Redis from RDB snapshot (if used)
4. Restart the stack: `docker compose up -d`
5. Verify health: `curl http://localhost:8080/health`

## Disaster Recovery

### RPO (Recovery Point Objective)
- Database: up to 24 hours (daily backups)
- Configuration: up to 24 hours (IaC)

### RTO (Recovery Time Objective)
- Full stack recovery: < 30 minutes
- Database restore: < 15 minutes (50 GB database)

## Data Export

```python
# Export all repository data
from eaip.shared.repository import InMemoryRepository

repo = InMemoryRepository(...)
async for item in repo.iter_all():
    # Export logic
    pass
```

## Data Persistence

EAIP uses in-memory repositories by default. For production:

1. Implement a PostgreSQL-backed `AbstractRepository`
2. Inject via DI container
3. All service code remains unchanged

The `AbstractRepository` interface ensures that adding persistence
requires no changes to business logic.
