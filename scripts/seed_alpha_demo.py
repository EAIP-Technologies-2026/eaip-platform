#!/usr/bin/env python3
"""EAIP Alpha Demo Data Seeding Script.

Uses ONLY the public HTTP APIs (exactly as the frontend does) to populate
agents, workflows, missions, knowledge assets, executions, and events.

Run against a live EAIP backend on localhost:8080.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8080/api"
LOGIN_BODY = {"username": "demo-seeder", "password": "seed-pass"}

AGENTS = [
    {
        "id": "agent-oncall-router",
        "name": "On-Call Router",
        "description": "Routes incident alerts to the correct on-call engineer based on severity and service ownership.",
        "tools": ["echo", "current_time"],
        "model": "stub",
        "metadata": {"owner": "platform-ops", "system_prompt": "You are an expert SRE routing agent."},
    },
    {
        "id": "agent-cost-optimizer",
        "name": "Cost Optimizer",
        "description": "Analyzes cloud spend patterns and recommends reserved-instance purchases and right-sizing actions.",
        "tools": ["echo", "current_time"],
        "model": "stub",
        "metadata": {"owner": "finops", "system_prompt": "You are a FinOps analyst."},
    },
    {
        "id": "agent-security-scanner",
        "name": "Security Scanner",
        "description": "Continuously scans infrastructure changes for CIS benchmark violations and exposed secrets.",
        "tools": ["echo"],
        "model": "stub",
        "metadata": {"owner": "security-team", "system_prompt": "You are a security compliance auditor."},
    },
    {
        "id": "agent-compliance-checker",
        "name": "Compliance Checker",
        "description": "Validates deployed resources against SOC2 and GDPR policy bundles before release.",
        "tools": ["echo", "current_time"],
        "model": "stub",
        "metadata": {"owner": "governance", "system_prompt": "You are a compliance officer."},
    },
    {
        "id": "agent-data-guardian",
        "name": "Data Guardian",
        "description": "Monitors data access logs, detects anomalous queries, and enforces masking policies.",
        "tools": ["echo"],
        "model": "stub",
        "metadata": {"owner": "data-platform", "system_prompt": "You are a data privacy agent."},
    },
    {
        "id": "agent-release-coordinator",
        "name": "Release Coordinator",
        "description": "Orchestrates blue-green deployments, health checks, and rollback decisions.",
        "tools": ["echo", "current_time"],
        "model": "stub",
        "metadata": {"owner": "devops", "system_prompt": "You are a release orchestration agent."},
    },
    {
        "id": "agent-knowledge-curator",
        "name": "Knowledge Curator",
        "description": "Indexes runbooks, post-mortems, and architecture decisions for semantic retrieval.",
        "tools": ["echo"],
        "model": "stub",
        "metadata": {"owner": "platform-eng", "system_prompt": "You are a knowledge management agent."},
    },
]

WORKFLOWS = [
    {
        "id": "wf-incident-response",
        "name": "Incident Response",
        "description": "End-to-end incident response: detect, route, remediate, and notify.",
        "steps": [
            {"id": "detect", "name": "Detect Anomaly", "agent_id": "agent-security-scanner", "tool_name": "echo", "prompt": "Scan for anomalies"},
            {"id": "route", "name": "Route Alert", "agent_id": "agent-oncall-router", "tool_name": "echo", "prompt": "Route to on-call"},
            {"id": "remediate", "name": "Auto-Remediate", "agent_id": "agent-release-coordinator", "tool_name": "echo", "prompt": "Execute remediation"},
            {"id": "notify", "name": "Notify Stakeholders", "agent_id": "agent-oncall-router", "tool_name": "current_time", "prompt": "Send status update"},
        ],
        "edges": [
            {"source": "detect", "target": "route", "label": "anomaly_found"},
            {"source": "route", "target": "remediate", "label": "acknowledged"},
            {"source": "remediate", "target": "notify", "label": "complete"},
        ],
    },
    {
        "id": "wf-cost-review",
        "name": "Monthly Cost Review",
        "description": "Generate a cost report, identify savings, and open right-sizing tickets.",
        "steps": [
            {"id": "gather", "name": "Gather Metrics", "agent_id": "agent-cost-optimizer", "tool_name": "current_time", "prompt": "Collect spend data"},
            {"id": "analyze", "name": "Analyze Trends", "agent_id": "agent-cost-optimizer", "tool_name": "echo", "prompt": "Identify waste"},
            {"id": "ticket", "name": "Open Tickets", "agent_id": "agent-compliance-checker", "tool_name": "echo", "prompt": "Create Jira tickets"},
        ],
        "edges": [
            {"source": "gather", "target": "analyze", "label": "data_ready"},
            {"source": "analyze", "target": "ticket", "label": "savings_found"},
        ],
    },
    {
        "id": "wf-compliance-audit",
        "name": "Compliance Audit",
        "description": "Run a full compliance audit across all tenants and produce an attestation report.",
        "steps": [
            {"id": "scan", "name": "Policy Scan", "agent_id": "agent-security-scanner", "tool_name": "echo", "prompt": "Scan resources"},
            {"id": "validate", "name": "Validate Controls", "agent_id": "agent-compliance-checker", "tool_name": "echo", "prompt": "Check controls"},
            {"id": "report", "name": "Generate Report", "agent_id": "agent-knowledge-curator", "tool_name": "echo", "prompt": "Draft attestation"},
        ],
        "edges": [
            {"source": "scan", "target": "validate", "label": "scanned"},
            {"source": "validate", "target": "report", "label": "validated"},
        ],
    },
    {
        "id": "wf-data-onboarding",
        "name": "Data Onboarding",
        "description": "Onboard a new dataset: classify, mask, index, and grant access.",
        "steps": [
            {"id": "classify", "name": "Classify Data", "agent_id": "agent-data-guardian", "tool_name": "echo", "prompt": "Classify sensitivity"},
            {"id": "mask", "name": "Apply Masking", "agent_id": "agent-data-guardian", "tool_name": "echo", "prompt": "Mask PII"},
            {"id": "index", "name": "Index for Search", "agent_id": "agent-knowledge-curator", "tool_name": "echo", "prompt": "Index documents"},
            {"id": "grant", "name": "Grant Access", "agent_id": "agent-compliance-checker", "tool_name": "echo", "prompt": "Approve access"},
        ],
        "edges": [
            {"source": "classify", "target": "mask", "label": "classified"},
            {"source": "mask", "target": "index", "label": "masked"},
            {"source": "index", "target": "grant", "label": "indexed"},
        ],
    },
]

MISSIONS = [
    {
        "id": "mission-sre-readiness",
        "name": "Q3 SRE Readiness Review",
        "agent_ids": ["agent-oncall-router", "agent-security-scanner", "agent-release-coordinator"],
        "workflow_ids": ["wf-incident-response"],
        "metadata": {"description": "Validate incident response pipelines ahead of Q3 scaling event."},
    },
    {
        "id": "mission-finops-sprint",
        "name": "FinOps Sprint — Cloud Waste Reduction",
        "agent_ids": ["agent-cost-optimizer", "agent-compliance-checker"],
        "workflow_ids": ["wf-cost-review"],
        "metadata": {"description": "Reduce cloud spend by 12%% this sprint."},
    },
    {
        "id": "mission-soc2-prep",
        "name": "SOC2 Type II Preparation",
        "agent_ids": ["agent-security-scanner", "agent-compliance-checker", "agent-data-guardian"],
        "workflow_ids": ["wf-compliance-audit"],
        "metadata": {"description": "Complete all SOC2 controls and generate attestation evidence."},
    },
    {
        "id": "mission-knowledge-launch",
        "name": "Enterprise Knowledge Base Launch",
        "agent_ids": ["agent-knowledge-curator", "agent-data-guardian"],
        "workflow_ids": ["wf-data-onboarding"],
        "metadata": {"description": "Launch the enterprise knowledge platform with curated runbooks."},
    },
]

KNOWLEDGE_COLLECTIONS = [
    {"name": "runbooks", "description": "Operational runbooks and playbooks."},
    {"name": "postmortems", "description": "Incident post-mortems and root-cause analyses."},
    {"name": "policies", "description": "Security, compliance, and data governance policies."},
]

KNOWLEDGE_DOCUMENTS = [
    {"title": "Incident Response Runbook v2.1", "content": "Step 1: Acknowledge page within 5 minutes. Step 2: Classify severity. Step 3: Execute remediation workflow.", "collection": "runbooks", "tags": ["sre", "incident"]},
    {"title": "AWS Cost Optimization Guide", "content": "Use Graviton3 for compute, move cold data to Glacier, enable Spot for batch workloads.", "collection": "runbooks", "tags": ["finops", "aws"]},
    {"title": "Post-Mortem — July Cache Outage", "content": "Root cause: stale TTL on edge cache. Remediation: circuit breaker added. Action items: 3.", "collection": "postmortems", "tags": ["outage", "cache"]},
    {"title": "SOC2 Control Matrix", "content": "CC6.1 — Logical access controls. CC7.2 — System monitoring. CC8.1 — Change management.", "collection": "policies", "tags": ["soc2", "compliance"]},
    {"title": "GDPR Data Handling Policy", "content": "Article 17 — Right to erasure. All personal data must be purged within 30 days of request.", "collection": "policies", "tags": ["gdpr", "privacy"]},
]

EVENTS = [
    {"type": "AgentCreated", "payload": {"agent_id": "agent-oncall-router", "name": "On-Call Router"}},
    {"type": "AgentCreated", "payload": {"agent_id": "agent-cost-optimizer", "name": "Cost Optimizer"}},
    {"type": "WorkflowCreated", "payload": {"workflow_id": "wf-incident-response", "name": "Incident Response"}},
    {"type": "MissionCreated", "payload": {"mission_id": "mission-sre-readiness", "name": "Q3 SRE Readiness Review"}},
    {"type": "KnowledgeDocumentIndexed", "payload": {"document_id": "doc-runbook-001", "title": "Incident Response Runbook v2.1"}},
    {"type": "DeploymentCompleted", "payload": {"service": "eaip-control-plane", "version": "0.0.2-alpha"}},
    {"type": "AlertFired", "payload": {"severity": "warning", "message": "High memory usage on agent-runtime pod-7"}},
    {"type": "AuditLogged", "payload": {"actor": "demo-seeder", "action": "seed_data", "resource": "platform"}},
]


class Seeder:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.token: str | None = None
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def login(self) -> None:
        resp = await self.client.post("/auth/login", json=LOGIN_BODY)
        resp.raise_for_status()
        data = resp.json()
        self.token = data["token"]
        print(f"[auth] logged in as {data['user']['name']}")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def create_agents(self) -> list[str]:
        created: list[str] = []
        for a in AGENTS:
            resp = await self.client.post("/agents", json=a, headers=self._headers())
            if resp.status_code in (200, 201):
                created.append(a["id"])
                print(f"[agent] created {a['id']}")
            elif resp.status_code == 409:
                print(f"[agent] already exists {a['id']}")
            else:
                print(f"[agent] failed {a['id']}: {resp.status_code} {resp.text}")
        return created

    async def execute_agents(self, agent_ids: list[str]) -> None:
        for aid in agent_ids[:5]:
            resp = await self.client.post(
                f"/agents/{aid}/execute",
                json={"input": f"Demo execution for {aid}"},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                print(f"[agent] executed {aid}")
            else:
                print(f"[agent] execute failed {aid}: {resp.status_code}")

    async def create_workflows(self) -> list[str]:
        created: list[str] = []
        for w in WORKFLOWS:
            resp = await self.client.post("/workflows", json=w, headers=self._headers())
            if resp.status_code in (200, 201):
                created.append(w["id"])
                print(f"[workflow] created {w['id']}")
            elif resp.status_code == 409:
                print(f"[workflow] already exists {w['id']}")
            else:
                print(f"[workflow] failed {w['id']}: {resp.status_code} {resp.text}")
        return created

    async def execute_workflows(self, wf_ids: list[str]) -> None:
        for wid in wf_ids:
            resp = await self.client.post(
                f"/workflows/{wid}/execute",
                json={},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                print(f"[workflow] executed {wid}")
            else:
                print(f"[workflow] execute failed {wid}: {resp.status_code}")

    async def create_missions(self) -> list[str]:
        created: list[str] = []
        for m in MISSIONS:
            resp = await self.client.post("/missions", json=m, headers=self._headers())
            if resp.status_code in (200, 201):
                created.append(m["id"])
                print(f"[mission] created {m['id']}")
            elif resp.status_code == 409:
                print(f"[mission] already exists {m['id']}")
            else:
                print(f"[mission] failed {m['id']}: {resp.status_code} {resp.text}")
        return created

    async def execute_missions(self, mission_ids: list[str]) -> None:
        for mid in mission_ids:
            resp = await self.client.post(
                f"/missions/{mid}/execute",
                json={},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                print(f"[mission] executed {mid}")
            else:
                print(f"[mission] execute failed {mid}: {resp.status_code}")

    async def create_knowledge(self) -> None:
        for col in KNOWLEDGE_COLLECTIONS:
            resp = await self.client.post("/knowledge/collections", json=col, headers=self._headers())
            if resp.status_code in (200, 201):
                print(f"[knowledge] created collection {col['name']}")
            else:
                print(f"[knowledge] collection failed {col['name']}: {resp.status_code}")

        for doc in KNOWLEDGE_DOCUMENTS:
            resp = await self.client.post("/knowledge/documents", json=doc, headers=self._headers())
            if resp.status_code in (200, 201):
                print(f"[knowledge] created document {doc['title']}")
            else:
                print(f"[knowledge] document failed {doc['title']}: {resp.status_code}")

    async def publish_events(self) -> None:
        for evt in EVENTS:
            resp = await self.client.post("/events/publish", json=evt, headers=self._headers())
            if resp.status_code == 200:
                print(f"[event] published {evt['type']}")
            else:
                print(f"[event] publish failed {evt['type']}: {resp.status_code}")

    async def verify(self) -> dict:
        checks: dict[str, any] = {}

        r = await self.client.get("/agents", headers=self._headers())
        checks["agents"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/agents/stats", headers=self._headers())
        checks["agent_stats"] = r.json() if r.status_code == 200 else {}

        r = await self.client.get("/workflows", headers=self._headers())
        checks["workflows"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/workflows/stats", headers=self._headers())
        checks["workflow_stats"] = r.json() if r.status_code == 200 else {}

        r = await self.client.get("/missions", headers=self._headers())
        checks["missions"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/missions/stats", headers=self._headers())
        checks["mission_stats"] = r.json() if r.status_code == 200 else {}

        r = await self.client.get("/monitoring/events", headers=self._headers())
        checks["monitoring_events"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/monitoring/metrics", headers=self._headers())
        checks["monitoring_metrics"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/runtime/metrics", headers=self._headers())
        checks["runtime_metrics"] = r.json() if r.status_code == 200 else {}

        r = await self.client.get("/events/activity", headers=self._headers())
        checks["activity"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/knowledge/collections", headers=self._headers())
        checks["knowledge_collections"] = r.json() if r.status_code == 200 else []

        r = await self.client.get("/knowledge/documents", headers=self._headers())
        checks["knowledge_documents"] = r.json() if r.status_code == 200 else []

        return checks

    async def close(self) -> None:
        await self.client.aclose()


async def main() -> int:
    seeder = Seeder(BASE_URL)
    try:
        await seeder.login()

        agent_ids = await seeder.create_agents()
        await seeder.execute_agents(agent_ids)

        wf_ids = await seeder.create_workflows()
        await seeder.execute_workflows(wf_ids)

        mission_ids = await seeder.create_missions()
        await seeder.execute_missions(mission_ids)

        await seeder.create_knowledge()
        await seeder.publish_events()

        print("\n--- Verification ---")
        checks = await seeder.verify()
        print(f"Agents: {len(checks['agents'])}")
        print(f"Agent stats: {checks['agent_stats']}")
        print(f"Workflows: {len(checks['workflows'])}")
        print(f"Workflow stats: {checks['workflow_stats']}")
        print(f"Missions: {len(checks['missions'])}")
        print(f"Mission stats: {checks['mission_stats']}")
        print(f"Monitoring events: {len(checks['monitoring_events'])}")
        print(f"Monitoring metrics: {len(checks['monitoring_metrics'])}")
        print(f"Runtime metrics keys: {list(checks['runtime_metrics'].keys())}")
        print(f"Activity feed: {len(checks['activity'])}")
        print(f"Knowledge collections: {len(checks['knowledge_collections'])}")
        print(f"Knowledge documents: {len(checks['knowledge_documents'])}")

        ok = (
            len(checks["agents"]) >= 5
            and len(checks["workflows"]) >= 3
            and len(checks["missions"]) >= 3
            and len(checks["monitoring_events"]) > 0
            and len(checks["activity"]) > 0
        )
        return 0 if ok else 1
    finally:
        await seeder.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
