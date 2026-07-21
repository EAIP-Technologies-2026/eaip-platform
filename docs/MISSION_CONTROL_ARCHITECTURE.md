# Mission Control Architecture

## Overview

Mission Control is EAIP's operational nerve center. It provides real-time visibility into all platform activities, mission execution, runtime health, and system metrics.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Mission Control App                  │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │
│  │ Overview │ │ Missions │ │ Health │ │ Activity │ │
│  │ Dashboard│ │ List     │ │ Status  │ │ Feed     │ │
│  └────┬─────┘ └────┬─────┘ └───┬────┘ └────┬─────┘ │
│       │            │           │           │        │
└───────┼────────────┼───────────┼───────────┼────────┘
        │            │           │           │
   ┌────▼────────────▼───────────▼───────────▼────┐
   │               API Layer                       │
   │  /missions/*  /runtime/*  /events/*  /health │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │            Backend Services                    │
   │  MissionRegistry  AgentRegistry  WorkflowReg  │
   │  Runtime Metrics  HealthReporter  EventBus    │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │              WebSocket Bridge                   │
   │       EventBus → WebSocket → RealtimeProvider   │
   └─────────────────────────────────────────────────┘
```

## Key Components

### Backend
- `MissionRegistry` — CRUD and lifecycle for missions
- `Runtime Metrics` — aggregates agents, workflows, knowledge stats
- `Health Reporter` — service health aggregation
- `EventBus` → `WebSocket` — real-time event propagation

### Frontend
- **Overview Dashboard** — mission stats, runtime metrics, service health
- **Missions List** — all missions with status filtering
- **Health Status** — detailed service health breakdown
- **Activity Feed** — real-time event stream

## Realtime Updates

- WebSocket connection via `RealtimeProvider`
- `RealtimeSubscriber` auto-refreshes on events
- 30-second poll fallback for metrics
- Live indicators on dashboard

## API Endpoints

- `GET /missions/stats` — aggregate mission statistics
- `GET /missions` — list all missions
- `GET /runtime/metrics` — system resource metrics
- `GET /runtime/health` — service health status
- `GET /events/activity` — recent activity feed
