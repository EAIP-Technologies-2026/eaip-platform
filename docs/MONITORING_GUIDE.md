# Enterprise Monitoring Guide

## Overview

The Monitoring platform provides real-time observability into all EAIP services, infrastructure, and applications.

## Features

### Live Dashboard
- Real-time CPU, memory, disk, network metrics
- Database, Redis, Qdrant, MinIO health
- Worker, queue, API, WebSocket status
- Response time, errors, availability SLAs

### Log Explorer
- Live streaming logs with filtering and search
- JSON viewer with syntax highlighting
- Copy, download, and export capabilities
- Multi-source log aggregation

### Metrics & Charts
- Latency, requests, errors, traffic trending
- Memory, storage, queue depth visualization
- Active sessions, agents, knowledge, workflows, missions
- Historical trend analysis

### Alerts & Error Tracking
- Custom alert rules (critical/warning/info) with silencing, acknowledgement, and resolution.
- **Sentry** integration for error tracking and performance monitoring — configured via `EAIP_SENTRY_*` environment variables.

### Diagnostics
- Health reports with dependency graph
- Connection status for all services
- Configuration validation
- Startup and runtime validation

## API Endpoints

- `GET /live` - Liveness probe, 200 while the process is alive
- `GET /ready` - Readiness probe, 200 when critical/required dependencies are healthy or skipped
- `GET /health` - Full dependency report (healthy/skipped/degraded -> 200, unhealthy -> 503)
- `GET /monitoring/health` - Service health status with version info
- `GET /monitoring/metrics` - Aggregated platform metrics
- `GET /monitoring/logs` - Filtered log entries
- `GET /monitoring/alerts` - Active and historical alerts
- `GET /monitoring/diagnostics` - System diagnostic checks
- `GET /monitoring/events` - Platform event stream
