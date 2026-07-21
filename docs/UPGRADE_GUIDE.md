# EAIP Upgrade Guide — 0.1.0-rc.1

> **Last updated:** 2026-07-11

---

## Overview

This guide covers upgrading from previous versions of EAIP.

## Upgrading from Pre-Alpha (0.0.x)

### Breaking Changes

1. **JWT Secret Required**
   - `TokenService()` no longer defaults to `"eaip-auth-secret-default"`
   - **Action:** Set `EAIP_AUTH_SECRET` environment variable or pass `secret=` explicitly

2. **Event Publishing**
   - All domain events now published via EventBus
   - **Action:** Subscribers must register via `EventBus.subscribe()` instead of relying on side effects

3. **Repository Changes**
   - Token storage uses `InMemoryRepository` with bounded capacity
   - **Action:** No action required — backward compatible

4. **Pipeline Execution**
   - `execute_script()` now uses AST-validated `safe_exec()` instead of bare `exec()`
   - **Action:** Pipeline scripts must use only allowed operations (assignments, expressions, safe builtins)

5. **Command Execution**
   - `execute_command()` now uses `create_subprocess_exec` instead of `create_subprocess_shell`
   - **Action:** Ensure command targets reference actual executables, not shell builtins

### Deprecations

- `TokenService.__init__(secret="eaip-auth-secret-default")` — no longer a valid default

## Migration Steps

### Step 1: Environment Configuration

```bash
# Generate a secure JWT secret (256-bit)
openssl rand -hex 32

# Set required environment variables
export EAIP_AUTH_SECRET="your-256-bit-hex-secret"
export EAIP_ENVIRONMENT="production"
```

### Step 2: Database

```bash
# Create PostgreSQL database
createdb eaip

# Run migrations (when available)
python -m eaip migrate
```

### Step 3: Verify

```bash
# Run tests
make test

# Start the platform
python -m eaip

# Verify health
curl http://localhost:8080/health
```

## Rollback

```bash
# Revert to previous Docker image
docker compose -f docker-compose.yml down
docker compose -f docker-compose-previous.yml up -d
```
