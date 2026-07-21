# EAIP Release Notes — 0.1.0-rc.1

> **Release date:** 2026-07-11
> **Version:** 0.1.0-rc.1
> **Status:** Release Candidate

---

## Overview

EAIP (Enterprise Autonomous Intelligence Platform) is a composable, observable,
governed agent orchestration platform.  This is the first Release Candidate.

## What's Included

### Platform Foundation
- Ports & Adapters architecture (Hexagonal)
- In-process Event Bus with retry, hooks, metrics
- Dependency Injection container with cycle detection
- Health check framework with aggregated reporting
- Background task registry with graceful shutdown
- In-memory repository with TTL eviction and metrics
- Structured logging via LoggerPort
- Metrics collection via MetricsProvider
- Distributed tracing via TracingProvider

### Security
- JWT authentication with configurable TTL and refresh rotation
- Secret resolution via SecretProviderPort (env, file)
- AST-validated sandbox for safe code execution
- Subprocess execution via create_subprocess_exec
- No hardcoded credentials
- Bandit + pip-audit + detect-secrets in CI

### Authentication & Identity
- TokenService (JWT creation, validation, refresh, revocation)
- AuthenticationService with provider abstraction
- Identity store with session management
- Full lifecycle events (UserLoggedIn, UserLoggedOut, etc.)

### Agent Runtime
- Agent registry with versioning, status transitions, metadata
- Lifecycle: Draft → Registered → Ready → Running → Paused → Stopped → Archived
- Planner protocol (FixedPlanner, SimpleLLMPlanner)
- Guardrail protocol (CompositeGuardrail, NoopGuardrail)
- Step execution with retry

### Workflow Engine
- Workflow definition with DAG execution
- State machine with step lifecycle
- Parallel branch execution
- Approval checkpoints
- Parent/child workflow support
- Retry policies and timeout configuration

### Knowledge Platform
- Document ingestion pipeline (PDF, DOCX, MD, HTML, TXT)
- Configurable chunking (fixed-size, semantic, recursive)
- Embedding provider abstraction
- Vector store protocol with Qdrant implementation
- Hybrid search (semantic + keyword)
- Metadata filtering and pagination

### Mission Control
- Mission abstraction coordinating agents, workflows, knowledge
- Full lifecycle: Draft → Queued → Running → Completed/Failed/Cancelled
- Runtime registry tracking active components
- Infrastructure health checks
- Runtime diagnostics

### Production Adapters
- PostgreSQL (AbstractRepository)
- Redis (CacheProvider)
- MinIO/S3 (ObjectStorageProvider)
- OpenTelemetry (TracingProvider)
- Prometheus (MetricsProvider)
- Qdrant (VectorStore)

### Infrastructure
- Docker Compose (development + production)
- Health checks with startup ordering
- Environment configuration with validation
- Multi-tenancy via TenantContext
- Configuration profiles (dev/test/staging/production)
