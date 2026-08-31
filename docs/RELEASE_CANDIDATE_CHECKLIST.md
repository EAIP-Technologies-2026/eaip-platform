# Release Candidate Checklist

## Authentication & Authorization
- [x] Login/logout with JWT tokens
- [x] Session cookies (`eaip_session`) for middleware
- [x] Token refresh via `/auth/refresh`
- [x] Current user endpoint (`/users/me`, `/auth/me`)
- [x] Role checks (`eaip_roles` cookie)
- [x] Protected routes via Next.js middleware

## Dashboard
- [x] Enterprise Overview with stat cards
- [x] Real agent stats, workflow stats, knowledge stats
- [x] Runtime health panel with real data
- [x] Real-time event subscriptions (RealtimeSubscriber)

## Agents
- [x] Full CRUD (create, read, update, delete)
- [x] Archive, duplicate lifecycle
- [x] Execute, pause, resume, stop, retry
- [x] Execution history and events
- [x] Health check and aggregated statistics

## Workflows
- [x] Full CRUD (create, read, update, delete)
- [x] Archive, duplicate lifecycle
- [x] Execute, pause, resume, cancel, retry
- [x] Workflow designer persistence (save/load)
- [x] Autosave with recovery
- [x] Version management
- [x] Export/Import (JSON format)
- [x] Execution history

## Knowledge
- [x] Collection CRUD
- [x] Document CRUD with upload (XHR with progress)
- [x] Search with pagination
- [x] Activity tracking
- [x] Ingestion pipeline (chunking, embedding)

## Missions
- [x] Mission CRUD
- [x] Execution lifecycle
- [x] Statistics and aggregation
- [x] Analytics endpoints

## Administration
- [x] User management
- [x] Organization management
- [x] Role management
- [x] Audit logs
- [x] System settings (read/update)
- [x] Feature flags
- [x] API Keys management
- [x] License management
- [x] Deployment tracking

## Monitoring
- [x] Service health dashboard
- [x] Aggregated metrics
- [x] Log viewer
- [x] Alert management
- [x] System diagnostics
- [x] Queue monitoring

## Global Search
- [x] Global command palette (Ctrl+K)
- [x] Multi-source search
- [x] Recent/saved searches
- [x] Keyboard navigation

## Marketplace
- [x] Package browser
- [x] Publisher console
- [x] Category system
- [x] Installation management
- [x] Discovery carousel

## Realtime
- [x] WebSocket endpoint (`/ws`)
- [x] EventBus bridge to WebSocket
- [x] RealtimeProvider with auto-reconnect
- [x] RealtimeSubscriber for live refresh
- [x] Heartbeat (30s keepalive)
- [x] Channel subscribe/emit

## Persistence
- [x] PostgreSQL schema (18 tables)
- [x] Migration engine with rollback
- [x] PostgresRepository (JSONB adapter)
- [x] Database connection pool
- [x] Environment-based configuration

## Docker
- [x] Production docker-compose (API, Postgres, Redis, Qdrant)
- [x] Dev docker-compose
- [x] Health checks for all services
- [x] Volume mounts for data persistence

## Testing
- [x] 61 backend API integration tests
- [x] Unit tests for key service packages

## Performance
- [ ] Lighthouse CI integration
- [ ] Performance budget
- [ ] Bundle analysis
- [ ] Code splitting audit
- [ ] Lazy loading audit
- [ ] WebSocket load test
- [ ] API load test

## Accessibility
- [ ] WCAG 2.1 AA validation
- [ ] axe-core automated checks
- [ ] ARIA attributes
- [ ] Keyboard navigation
- [ ] Focus management
- [ ] Color contrast
- [ ] Screen reader testing
- [ ] Reduced motion support
