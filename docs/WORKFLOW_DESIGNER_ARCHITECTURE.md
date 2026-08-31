# Workflow Designer Architecture

## Overview

The Workflow Designer is a drag-and-drop visual IDE for creating enterprise workflows. It follows a client-server architecture with real-time autosave and versioning.

## Architecture

```
Frontend (React/Next.js)                Backend (FastAPI)
─────────────────────                    ────────────────
WorkflowDesigner.tsx  ◄── REST/WS ──►   /designer/* endpoints
    │                                      ├── PUT /{id} (save)
    │                                      ├── GET /{id} (load)
    ├── useWorkflowDesigner (hook)         ├── POST /{id}/autosave
    │   ├── save()                         ├── GET /{id}/autosave
    │   ├── load()                         └── DEL /{id}/autosave
    │   ├── autosave()                   
    │   └── discardAutosave()          WorkflowRegistry (persistence)
    │
    ├── WorkflowVersionHistory           WorkflowEngine (execution)
    └── WorkflowExecutionConsole
```

## Persistence

The designer persists:
- **Nodes** — canvas node definitions with type, label, position, config
- **Edges** — connections between nodes with conditions
- **Viewport** — camera position, zoom level, pan offset
- **Variables** — workflow-scoped variables
- **Secrets** — encrypted secret references
- **Tags/Labels** — metadata for organization

## Versioning

Every save creates a version entry:
- `workflow_versions` table tracks all versions
- Each version stores a complete snapshot
- Versions can be Draft, Published, or Archived
- Rollback restores a previous version's state
- Export/Import uses JSON format (`eaip-workflow-v1`)

## Autosave

- Triggers every 5 seconds when changes are detected
- Stores in-memory on the backend (recoverable after browser refresh)
- Cleared on explicit save
- Recovery prompt shown when unsaved autosave exists

## Node Types

11 supported node types: Start, End, Agent, Knowledge, Decision, Delay, Loop, Condition, Webhook, Approval, Parallel.
