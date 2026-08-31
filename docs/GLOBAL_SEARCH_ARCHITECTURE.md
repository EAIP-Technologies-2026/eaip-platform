# Global Search Architecture

## Overview

Global Search provides enterprise-wide intelligent search across all EAIP domains. One search box searches the entire platform.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  GlobalSearch UI                  │
│   (Command Palette: Ctrl+K / Click Search Icon)  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              Search API (/search/*)               │
│     Query → Federated Search → Ranked Results    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│           EnterpriseSearchEngine                  │
│   ├── KnowledgeSearchProvider                    │
│   ├── MemorySearchProvider                       │
│   ├── CompositeSearchProvider                    │
│   └── SearchFederation (multi-source merge)      │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              RankingService                       │
│    Relevance (0.6) + Recency (0.2) + Popularity  │
└─────────────────────────────────────────────────┘
```

## Search Sources

- Agents, Knowledge, Documents, Workflows
- Missions, Organizations, Users, Deployments
- Events, Audit Logs, Runtime Logs
- Settings, Marketplace

## Features

- Instant search with incremental results
- Ranking with relevance, recency, popularity scoring
- Search highlighting and category grouping
- Recent searches and saved searches
- Search suggestions and autocomplete
- Keyboard shortcuts (Ctrl+K, ↑↓ navigation, Enter to open, Esc to close)

## API Endpoints

- `GET /search?q=...` - Full-text search across all sources
- `GET /search/suggestions?q=...` - Autocomplete suggestions
- `GET /search/recent` - Recent searches
- `POST /search/recent` - Save recent search
- `GET /search/saved` - Saved searches
- `POST /search/saved` - Save a search
