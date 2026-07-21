# EAIP Production Checklist

> **Status:** Alpha → Beta
> **Last updated:** 2026-07-11

---

## Pre-Deployment

### Security
- [ ] `EAIP_AUTH_SECRET` is a 256-bit random value, not a default
- [ ] `EAIP_DB_PASSWORD` is a strong random password
- [ ] All secrets loaded via environment variables, not hardcoded
- [ ] JWT signing algorithm is HS256 or stronger
- [ ] Token TTLs are configured (default: 15 min access, 24 hr refresh)
- [ ] Rate limiting is configured on API gateway
- [ ] CORS origins are restricted to known domains
- [ ] `make security` passes (bandit + pip-audit)

### Infrastructure
- [ ] Database is a managed service with PITR enabled
- [ ] Redis has persistence enabled (AOF or RDB)
- [ ] Object storage (MinIO/S3) is configured for artifacts
- [ ] TLS certificates are provisioned and auto-renewing
- [ ] Health check endpoints are registered with orchestrator

### Configuration
- [ ] `EAIP_ENVIRONMENT` is set to `production`
- [ ] `EAIP_LOG_LEVEL` is set to `INFO` or `WARNING`
- [ ] Database connection pool limits are configured
- [ ] Redis connection pool limits are configured
- [ ] API rate limits are configured per tenant
- [ ] Backup schedule is configured

## Deployment

### Docker
- [ ] `docker compose build` succeeds
- [ ] `docker compose up -d` starts all services
- [ ] Health checks pass: `docker compose ps`
- [ ] API responds: `curl http://localhost:8080/health`

### Kubernetes
- [ ] Liveness probe configured (path: `/health`, port: 8080)
- [ ] Readiness probe configured (path: `/ready`, port: 8080)
- [ ] Resource limits set (CPU/Memory)
- [ ] Horizontal Pod Autoscaler configured
- [ ] Secrets stored in Kubernetes Secrets or external vault
- [ ] Pod Disruption Budget configured
- [ ] Network policies restrict pod-to-pod traffic

## Post-Deployment

### Verification
- [ ] Login flow works end-to-end
- [ ] Token refresh works
- [ ] Knowledge upload and search work
- [ ] Agent execution works
- [ ] Workflow execution works
- [ ] Mission lifecycle works
- [ ] Health endpoint returns 200
- [ ] Structured logs are emitted in JSON format
- [ ] Metrics are being collected

### Monitoring
- [ ] Log aggregation is configured
- [ ] Metrics are being scraped (Prometheus/OTel)
- [ ] Alerts are configured for:
  - API down
  - High error rate (>1%)
  - High latency (p95 > 500ms)
  - Disk space < 20%
- [ ] Dashboard is created showing:
  - Request rate and latency
  - Error rate by endpoint
  - Active sessions
  - Background task count
  - Queue depth

### Operations
- [ ] Backup schedule is active
- [ ] Backup restore procedure is documented
- [ ] On-call runbook is created
- [ ] Incident response plan is documented
- [ ] DB migration procedure is tested
- [ ] Rollback procedure is tested

## Scaling

| Component | Scale Strategy |
|-----------|---------------|
| EAIP API | Horizontal (stateless) — add replicas |
| PostgreSQL | Vertical (read replicas for queries) |
| Redis | Cluster mode (sharding) |
| Qdrant | Cluster mode (sharding + replication) |
| Background Workers | Horizontal — add worker pods |

## Performance Baselines

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| API p95 latency | < 100ms | > 500ms | > 1s |
| Knowledge search p95 | < 200ms | > 1s | > 3s |
| Agent execution p95 | < 5s | > 30s | > 60s |
| Workflow execution p95 | < 10s | > 60s | > 120s |
| Event bus latency p95 | < 10ms | > 50ms | > 100ms |
| Token validation p95 | < 5ms | > 20ms | > 50ms |
