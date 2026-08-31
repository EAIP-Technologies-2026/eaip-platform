# EAIP Beta Release Notes

## Version 0.1.0-beta

Enterprise Autonomous Intelligence Platform — Beta Release Candidate.

## What's New

### Enterprise Workspaces
- **Dashboard** — Real-time enterprise overview with live metrics, agent stats, workflow stats, health monitoring
- **Mission Control** — Operations center with mission tracking, runtime metrics, service health, activity feed
- **Monitoring** — Service health dashboard, metrics, log explorer, alerts, diagnostics
- **Administration** — User management, organization management, roles & permissions, audit logs, API keys, system settings, feature flags, license management
- **Marketplace** — Package browser, publisher console, discovery, installation management

### Agent Platform
- Full agent lifecycle (create, read, update, delete, archive, duplicate)
- Agent execution with pause/resume/stop/retry
- Execution history and event tracking
- Health monitoring and aggregated statistics

### Workflow Platform
- Visual workflow designer with drag-and-drop canvas (11 node types)
- Full CRUD with version management
- Autosave with browser recovery
- Workflow execution with state machine
- Export/import (EAIP JSON format)
- Version history with publish/archive/rollback

### Knowledge Platform
- Document ingestion pipeline (chunking, embedding, vector storage)
- Collection management
- Semantic search with pagination
- File upload with progress tracking
- Activity timeline

### Global Search
- Enterprise-wide search across all domains
- Recent and saved searches
- Keyboard shortcuts (Ctrl+K)

### Real-time Platform
- WebSocket infrastructure with auto-reconnect
- EventBus bridge for live updates
- Channel-based pub/sub
- Realtime dashboard refresh

### Authentication & Security
- JWT-based authentication with token refresh
- Session cookies for middleware
- Role-based access control
- Session management

### Infrastructure
- PostgreSQL production schema (18 tables)
- Migration engine with rollback
- Redis caching adapter
- Docker Compose deployment (API, PostgreSQL, Redis, Qdrant)
- Health monitoring for all services

## Architecture
- Hexagonal architecture with ports and adapters
- Domain-driven design with frozen models
- EventBus for in-process event propagation
- Dependency injection throughout
- Repository pattern with environment-based selection

## Known Limitations
- WebSocket `PushService` stores messages but doesn't actively push over socket (EventBus→WS bridge works)
- Services use in-memory storage by default; PostgreSQL requires `production` environment
- Some pages (Automation, Admin) still use hardcoded data via package component props
- Standalone apps (mission-control, administration) not yet integrated into main navigation
