# EAIP Known Limitations (Beta)

## Functional Limitations

### PushService Active Delivery
The `PushService.push()` method now registers active socket senders for real-time delivery. However, if no WebSocket connection is currently active for a user, messages will be queued in a pending buffer rather than persisted for later retrieval.

### In-Memory Persistence (Development)
When `EAIP_CORE__ENVIRONMENT` is set to `local` or `testing`, all services use `InMemoryRepository` instead of `PostgresRepository`. This means data is lost on restart. Set environment to `production` or `staging` for persistent storage.

### Automation Page Hardcoded Data
The Automation workspace (`@eaip/automation` package components) receives data via component props with hardcoded defaults. The `WorkflowCanvas`, `NodePalette`, and `Scheduler` components render example data when no API data is available.

### Standalone App Integration
The `mission-control`, `administration`, `workspace`, and `mobile` apps are built as separate Next.js applications. They are NOT integrated into the main enterprise console navigation. Each runs independently.

### WebSocket PushService Pending Buffer
Messages queued in the `PushService._pending` buffer are held in memory only. A process restart will lose pending messages. Production deployments should use Redis-backed message persistence.

## Technical Debt

### Dependency Declarations
- `asyncpg` is imported lazily in `PostgresRepository` but not declared in `pyproject.toml`
- `redis` is imported lazily in `RedisCacheProvider` but not declared in `pyproject.toml`

### Test Coverage
- 98 integration tests cover API endpoints
- 9,000+ unit tests cover service logic
- No WebSocket integration tests
- No Playwright E2E tests for authenticated flows
- No visual regression tests

### Accessibility
- WCAG 2.1 AA compliance has not been externally audited
- axe-core automated checks not integrated into CI
- Screen reader testing not yet performed

### Performance
- Lighthouse CI not integrated
- No performance budget enforced
- Bundle analysis not automated
- No load testing results available

## Security

### CORS Configuration
Currently allows all origins (`allow_origins=["*"]`). Production deployments should restrict to specific origins.

### Secret Management
JWT signing secret configured via environment variable (`EAIP_AUTH_SECRET`). No vault integration. Secrets currently passed in code for development convenience.

## Planned for GA

1. PushService Redis-backed message persistence
2. Full PostgreSQL DI wiring in production
3. Standalone app integration into main navigation
4. WCAG 2.1 AA external audit
5. Lighthouse CI with performance budget
6. WebSocket load testing
7. Security audit and penetration testing
8. Vault/secret management integration
9. Kubernetes deployment manifests
10. Multi-region disaster recovery
