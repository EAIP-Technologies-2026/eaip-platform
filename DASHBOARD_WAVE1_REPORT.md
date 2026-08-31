# Dashboard Sprint — Wave 1 Completion Report

## Summary
Wave 1 fixed three blocking stubs/misroutes that prevented the dashboard from showing live data for monitoring, knowledge activity, and mission logs.

## Commit 1: Fix Monitoring Route Shadowing
- **Root cause:** `monitoring.py` (stub endpoints returning hardcoded zeros) was registered BEFORE `monitoring_routes.py` (real endpoints using Prometheus metrics), causing FastAPI to route all `/monitoring/*` requests to the stubs.
- **Fix:** Removed `monitoring` from the import list and `app.include_router(monitoring.router)` from `eaip/http/api.py`.
- **Result:** `/monitoring/health`, `/monitoring/metrics`, `/monitoring/logs` now hit the real `monitoring_routes.py` handlers.
- **Verification:** `TestMonitoring::test_monitoring_health/metrics/logs` all pass. Manual curl shows real Prometheus registry counts.

## Commit 2: Wire Knowledge Activity to EventStore
- **File:** `eaip/http/routers/knowledge.py`
- **Change:** `GET /knowledge/activity` now calls `EventStore.recent_by(type="knowledge")` instead of returning `[]`.
- **How it works:** Events published from `eaip.knowledge.*` modules are classified as `type="knowledge"` by `EventStore._classify()` and stored with `_classified_type` field. The endpoint queries these via the container-resolved EventStore instance.
- **Pre-existing issue:** All knowledge endpoints require auth (`Depends(get_current_user)`). The integration test (`test_knowledge_activity`) asserts 200 without providing a token, failing with 401. This is a pre-existing test issue, not a regression.

## Commit 3: Wire Mission Logs to EventStore
- **File:** `eaip/http/routers/missions.py`
- **Change:** `GET /missions/{mission_id}/logs` now calls `EventStore.recent_by(mission_id=mission_id)` instead of returning `[]`.
- **Supporting change:** `eaip/events/store.py` — added `_mission_id` field to `EventStore.record()` and `mission_id` filter parameter to `EventStore.recent_by()`.
- **Conservative approach:** No existing schema changed; `_mission_id` defaults to `None` for events without it. Backward compatible.

## Test Results
| Suite | Tests | Status |
|---|---|---|
| Monitoring integration | 3 | ✅ All pass |
| Monitoring stabilization | 2 | ✅ All pass |
| Event flow integration | 6 | ✅ All pass |
| Event demo e2e | 3 | ✅ All pass |
| Event sourcing store | 20 | ✅ All pass |
| Knowledge activity | 1 | ❌ 401 (pre-existing auth in test) |

## Next
Proceed to Wave 2: Wire agent stats route + workflow run metrics + event activity to live EventStore data.
