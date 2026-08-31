# EAIP Deployment Guide

> **Status:** Alpha → Beta
> **Last updated:** 2026-07-11

---

## Prerequisites

- Docker 24+ and Docker Compose v2+
- Python 3.11+
- 4 GB RAM minimum (8 GB recommended)
- PostgreSQL 16 (managed service preferred)
- Redis 7 (managed service preferred)
- Qdrant (optional, for vector search)

## Quick Start (Development)

```bash
# Clone and bootstrap
git clone <repo> eaip-platform
cd eaip-platform
make bootstrap

# Run tests
make test

# Start dev environment
docker compose -f docker-compose.dev.yml run --rm eaip
```

## Production Deployment

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EAIP_ENVIRONMENT` | No | `production` | Runtime environment |
| `EAIP_AUTH_SECRET` | **Yes** | — | JWT signing secret (256-bit) |
| `EAIP_DB_PASSWORD` | **Yes** | — | PostgreSQL password |
| `EAIP_HTTP_PORT` | No | `8080` | HTTP listen port |
| `EAIP_LOG_LEVEL` | No | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `EAIP_DB_NAME` | No | `eaip` | Database name |
| `EAIP_DB_USER` | No | `eaip` | Database user |
| `EAIP_DB__HOST` | No | `postgres` | Database host |
| `EAIP_DB__PORT` | No | `5432` | Database port |
| `EAIP_REDIS__HOST` | No | `redis` | Redis host |
| `EAIP_REDIS__PORT` | No | `6379` | Redis port |
| `EAIP_QDRANT__HOST` | No | `qdrant` | Qdrant host |
| `EAIP_QDRANT__PORT` | No | `6333` | Qdrant port |

### Docker Compose (Production)

```bash
export EAIP_AUTH_SECRET="your-256-bit-secret"
export EAIP_DB_PASSWORD="your-db-password"
docker compose up -d
```

### Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness probe — returns 200 if alive |
| `GET /ready` | Readiness probe — returns 200 when all backends connected |

### Startup Order

1. PostgreSQL (health check: `pg_isready`)
2. Redis (background)
3. Qdrant (background)
4. EAIP API (waits for PostgreSQL)

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eaip
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eaip
  template:
    metadata:
      labels:
        app: eaip
    spec:
      containers:
      - name: eaip
        image: eaip-platform:latest
        ports:
        - containerPort: 8080
        env:
        - name: EAIP_AUTH_SECRET
          valueFrom:
            secretKeyRef:
              name: eaip-secrets
              key: auth-secret
        - name: EAIP_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: eaip-secrets
              key: db-password
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Configuration Profiles

| Profile | File | Purpose |
|---------|------|---------|
| `development` | `.env` | Local development with hot-reload |
| `testing` | `.env.test` | CI/CD test runs |
| `staging` | `.env.staging` | Pre-production validation |
| `production` | `.env.production` | Production workloads |
