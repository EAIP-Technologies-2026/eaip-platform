# Dashboard Sprint — Wave 2 Completion Report

## Summary
Wave 2 completes the remaining core dashboard metrics so the Enterprise Console displays live operational data instead of placeholder values. Agent stats, workflow stats, and knowledge stats were already live from prior work; this wave focused on the remaining stubs in monitoring, runtime metrics, and event endpoints.

## Files Modified

| File | Change |
|---|---|
| `src/eaip/http/routers/monitoring_routes.py` | Wired `/monitoring/events` to EventStore; fixed `/monitoring/metrics` uptime (was hardcoded `"0s"`, now computed from `_start_time`) |
| `src/eaip/http/routers/runtime.py` | Wire `avgLatencyMs` in `/runtime/metrics` from AgentRuntime run records; remove `eventThroughput` and `activeUsers` (not computable from current data) |

## APIs Connected

| Endpoint | Status Before | Status After | Source |
|---|---|---|---|
| `GET /agents/stats` | LIVE (already from registry + runtime) | LIVE (unchanged) | AgentRegistry, AgentRuntime |
| `GET /agents/health` | LIVE (already from runtime.health()) | LIVE (unchanged) | AgentRuntime.health() |
| `GET /workflows/stats` | LIVE (already from registry + engine) | LIVE (unchanged) | WorkflowRegistry, WorkflowEngine |
| `GET /workflows/health` | LIVE (already from engine) | LIVE (unchanged) | WorkflowEngine |
| `GET /knowledge/stats` | LIVE (already from registry) | LIVE (unchanged) | KnowledgeRegistry |
| `GET /missions/stats` | LIVE (already from registry) | LIVE (unchanged) | MissionRegistry |
| `GET /runtime/metrics` | PARTIAL (`avgLatencyMs: 0` hardcoded) | LIVE (computed from AgentRuntime runs) | AgentRuntime |
| `GET /monitoring/metrics` | PARTIAL (`uptime: "0s"` hardcoded) | LIVE (computed from app start time) | `request.app.state._start_time` |
| `GET /monitoring/events` | **STUB** (returned `[]`) | LIVE (returns EventStore events) | EventStore |
| `GET /monitoring/health` | LIVE | LIVE (unchanged) | HealthReporter |
| `GET /monitoring/logs` | STUB (single hardcoded entry) | STUB (unchanged — no centralized log store) | — |
| `GET /monitoring/alerts` | STUB (empty `[]`) | STUB (unchanged — no alert system) | — |
| `GET /monitoring/queues` | STUB (empty `[]`) | STUB (unchanged — no queue system) | — |
| `GET /events/activity` | LIVE (EventStore) | LIVE (unchanged) | EventStore |
| `GET /agents/{id}/events` | LIVE (EventStore) | LIVE (unchanged) | EventStore |
| `GET /workflows/{id}/events` | LIVE (EventStore) | LIVE (unchanged) | EventStore |

## Tests Executed

| Test Suite | Tests | Result |
|---|---|---|
| `TestMonitoring` (integration) | 3 | ✅ All pass |
| `TestMonitoringEndpoints` (stabilization) | 2 | ✅ All pass |
| `TestEventFlow` (integration) | 6 | ✅ All pass |
| `TestEventDemo` (e2e) | 3 | ✅ All pass |
| `TestKnowledgeE2E` | 1 | ✅ Pass |
| `TestKnowledgeLifecycleIntegration` | 6 | ✅ All pass |
| `TestKnowledgePipeline` | 9 | ✅ All pass |
| `TestMissionLifecycle` | 6 | ✅ All pass |
| `TestMissionEvents` | 2 | ✅ All pass |
| `TestRuntimeRegistry` | 5 | ✅ All pass |
| `TestPlatformConvergence` | 1 | ✅ Pass |
| `TestAgents`, `TestWorkflows`, `TestMissions`, `TestKnowledge` (auth-required) | ~20 | ❌ Pre-existing 401 failures (tests send no auth token) |

## Manual Verification

All endpoints return `200 OK` with correct response shapes. Key results:

- `GET /agents/stats` → `{"totalAgents": 0, "runningAgents": 0, ...}` (empty but correct shape)
- `GET /workflows/stats` → `{"totalWorkflows": 0, "activeCount": 0, ...}`
- `GET /runtime/metrics` → `{"avgLatencyMs": 0, "runningAgents": 0, ...}` (latency now computed from runtime)
- `GET /monitoring/events?limit=5` → returns 5 real EventStore events (previously `[]`)
- `GET /monitoring/metrics` → uptime now reflects actual app start time
- `GET /events/activity` → returns 8 platform startup events

## Remaining Dashboard Gaps

| KPI | Endpoint | Reason Not Computable |
|---|---|---|
| `avgTokensPerRun` | `GET /agents/stats` | `RunRecord` does not track token usage; requires changes to AgentRuntime.RunRecord schema |
| `activeUsers` | `GET /agents/stats` | No active user session tracking in the platform |
| `tokensUsedTotal` | `GET /agents/health` | Same as `avgTokensPerRun` — no token tracking |
| `totalStorage` | `GET /knowledge/stats` | Knowledge documents are in-memory; no storage tracking implemented |
| `monitoring/logs` | `GET /monitoring/logs` | No centralized log aggregation store; returns a single hardcoded entry |
| `monitoring/alerts` | `GET /monitoring/alerts` | No alerting subsystem implemented |
| `monitoring/queues` | `GET /monitoring/queues` | No message queue subsystem implemented |

All remaining gaps return `0` or `[]` as meaningful defaults — they do not fabricate values.

## Technical Debt Discovered

1. **Auth tokens in integration tests** — `TestAgents`, `TestWorkflows`, `TestMissions`, `TestKnowledge` suites all fail with 401 because they assert `status_code == 200` without providing a Bearer token. These tests send requests to endpoints guarded by `Depends(get_current_user)`. The tests need to be updated to authenticate first (or the test infrastructure needs an auth fixture).
2. **WorkflowEngine._runs is private** — `workflows.py` accesses `engine._runs` directly rather than through a public API. This is a pre-existing pattern but should be formalized.
3. **RunRecord lacks token tracking** — `avgTokensPerRun` and `tokensUsedTotal` cannot be computed because `RunRecord` (in `agents/runtime.py`) has no `tokens_used` field. Adding this requires schema changes.
