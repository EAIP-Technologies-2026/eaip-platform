# Playwright E2E Testing Guide

## Overview
Playwright tests verify EAIP works correctly across browsers (Chromium, Firefox, WebKit) at the user interaction level.

## Test Structure
Tests are in `apps/enterprise-console/e2e/`:

```
e2e/
  auth.spec.ts        # Login, logout, session, protected routes
  navigation.spec.ts  # Sidebar, page routing, headings
  knowledge.spec.ts   # Knowledge page tabs and interactions
  agents.spec.ts      # Agent CRUD and execution  
  workflows.spec.ts   # Workflow CRUD and designer
  missions.spec.ts    # Mission CRUD and execution
  admin.spec.ts       # Admin page tabs
  monitoring.spec.ts  # Monitoring dashboard
  search.spec.ts      # Global search
  realtime.spec.ts    # WebSocket connection
  accessibility.spec.ts  # WCAG compliance checks
```

## Running Tests

```bash
# All tests
cd apps/enterprise-console
pnpm exec playwright test

# Specific browser
pnpm exec playwright test --browser=firefox

# With UI
pnpm exec playwright test --ui

# Debug mode
pnpm exec playwright test --debug
```

## CI Integration
Playwright runs in CI via the `e2e` job in `.github/workflows/ci.yml`:
- Builds application
- Starts web server
- Runs tests against Chromium
- Retries failed tests twice

## Adding Tests
```typescript
import { test, expect } from "@playwright/test";

test("description", async ({ page }) => {
  await page.goto("/path");
  await expect(page.getByRole("heading")).toBeVisible();
});
```

## Visual Regression
```bash
pnpm exec playwright test --update-snapshots  # Update baselines
pnpm exec playwright test  # Compare against baselines
```
