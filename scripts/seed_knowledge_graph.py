#!/usr/bin/env python3
"""EAIP Knowledge Graph Synthetic Seeder.

Creates synthetic graph entities and relationships for three enterprises:
- Apex Advisory Group
- Nova Manufacturing Systems
- Meridian Health Services

Uses the public HTTP APIs (exactly as the frontend does) with tenant-isolated
authentication. Each enterprise's graph data is scoped to its authenticated user.

Run against a live EAIP backend on localhost:8080.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import httpx

BASE_URL = "http://localhost:8080/api"

# Login credentials for each enterprise
LOGIN_CREDENTIALS = {
    "apex": {"username": "apex-user", "password": "seed-pass"},
    "nova": {"username": "nova-user", "password": "seed-pass"},
    "meridian": {"username": "meridian-user", "password": "seed-pass"},
}


# ── Apex Advisory Group ──────────────────────────────────────────────

APEX_ENTITIES = [
    {
        "id": "org-apex",
        "type": "organization",
        "name": "Apex Advisory Group",
        "description": "Strategic consulting and advisory firm for enterprise transformation.",
        "tags": ["consulting", "strategy", "advisory"],
    },
    {
        "id": "person-caarter",
        "type": "person",
        "name": "Catherine Aarter",
        "description": "Senior Managing Partner, leads advisory services division.",
        "tags": ["partner", "executive"],
    },
    {
        "id": "person-jreed",
        "type": "person",
        "name": "James Reed",
        "description": "Director of Digital Transformation.",
        "tags": ["director", "transformation"],
    },
    {
        "id": "agent-apex1",
        "type": "agent",
        "name": "Strategic Advisor",
        "description": "Provides strategic guidance to client organizations.",
        "tags": ["advisor", "strategy"],
    },
    {
        "id": "agent-apex2",
        "type": "agent",
        "name": "Transformation Lead",
        "description": "Leads enterprise transformation initiatives.",
        "tags": ["lead", "transformation"],
    },
    {
        "id": "document-apex1",
        "type": "document",
        "name": "Transformation Framework v3.0",
        "description": "Comprehensive framework for organizational transformation.",
        "tags": ["framework", "transformation"],
    },
    {
        "id": "knowledge-apex1",
        "type": "knowledge",
        "name": "Enterprise Architecture Knowledge Base",
        "description": "Curated knowledge assets for enterprise architecture patterns.",
        "tags": ["architecture", "knowledge-base"],
    },
    {
        "id": "workflow-apex1",
        "type": "workflow",
        "name": "Onboarding Workflow",
        "description": "New hire onboarding and orientation process.",
        "tags": ["onboarding", "hr"],
    },
    {
        "id": "mission-apex1",
        "type": "mission",
        "name": "Q4 Strategic Review",
        "description": "Quarterly strategic review and goal-setting initiative.",
        "tags": ["strategy", "quarterly"],
    },
]

APEX_RELATIONSHIPS = [
    {
        "id": "rel-apex-org-employs",
        "type": "employs",
        "sourceEntityId": "org-apex",
        "targetEntityId": "person-caarter",
        "weight": 1.0,
    },
    {
        "id": "rel-apex-org-employs-2",
        "type": "employs",
        "sourceEntityId": "org-apex",
        "targetEntityId": "person-jreed",
        "weight": 1.0,
    },
    {
        "id": "rel-apex-agent-manages",
        "type": "manages",
        "sourceEntityId": "agent-apex1",
        "targetEntityId": "workflow-apex1",
        "weight": 0.9,
    },
    {
        "id": "rel-apex-agent-manages-2",
        "type": "manages",
        "sourceEntityId": "agent-apex2",
        "targetEntityId": "workflow-apex1",
        "weight": 0.85,
    },
    {
        "id": "rel-apex-agent-advises",
        "type": "advises",
        "sourceEntityId": "agent-apex1",
        "targetEntityId": "person-caarter",
        "weight": 0.95,
    },
    {
        "id": "rel-apex-doc-informs",
        "type": "informs",
        "sourceEntityId": "document-apex1",
        "targetEntityId": "agent-apex1",
        "weight": 0.9,
    },
    {
        "id": "rel-apex-knowledge-relates",
        "type": "relates_to",
        "sourceEntityId": "knowledge-apex1",
        "targetEntityId": "document-apex1",
        "weight": 0.95,
    },
    {
        "id": "rel-apex-mission-belongs",
        "type": "belongs_to",
        "sourceEntityId": "mission-apex1",
        "targetEntityId": "org-apex",
        "weight": 1.0,
    },
    {
        "id": "rel-apex-person-leads",
        "type": "leads",
        "sourceEntityId": "person-caarter",
        "targetEntityId": "agent-apex1",
        "weight": 0.95,
    },
]


# ── Nova Manufacturing Systems ───────────────────────────────────────

NOVA_ENTITIES = [
    {
        "id": "org-nova",
        "type": "organization",
        "name": "Nova Manufacturing Systems",
        "description": "Precision manufacturing and industrial equipment provider.",
        "tags": ["manufacturing", "industrial", "equipment"],
    },
    {
        "id": "person-qengineer",
        "type": "person",
        "name": "Quality Engineer",
        "description": "Responsible for product quality and compliance standards.",
        "tags": ["engineer", "quality"],
    },
    {
        "id": "person-scanalyst",
        "type": "person",
        "name": "Supply Chain Analyst",
        "description": "Analyzes supply chain efficiency and optimization opportunities.",
        "tags": ["analyst", "supply-chain"],
    },
    {
        "id": "agent-nova1",
        "type": "agent",
        "name": "Production Scheduler",
        "description": "Schedules production runs and optimizes resource allocation.",
        "tags": ["scheduler", "production"],
    },
    {
        "id": "agent-nova2",
        "type": "agent",
        "name": "Quality Control Agent",
        "description": "Monitors quality metrics and enforces compliance.",
        "tags": ["quality", "compliance"],
    },
    {
        "id": "doc-nova1",
        "type": "document",
        "name": "CNC SOP",
        "description": "Standard operating procedure for CNC machining operations.",
        "tags": ["sop", "cnc", "machining"],
    },
    {
        "id": "doc-nova2",
        "type": "document",
        "name": "Quality Report Q3",
        "description": "Quarterly quality performance report.",
        "tags": ["report", "quality", "q3"],
    },
    {
        "id": "knowledge-nova1",
        "type": "knowledge",
        "name": "Manufacturing Excellence Knowledge Base",
        "description": "Best practices and lessons learned in manufacturing optimization.",
        "tags": ["manufacturing", "excellence"],
    },
    {
        "id": "workflow-nova1",
        "type": "workflow",
        "name": "Quality Workflow",
        "description": "End-to-end quality inspection and improvement process.",
        "tags": ["quality", "workflow"],
    },
    {
        "id": "mission-nova1",
        "type": "mission",
        "name": "Cost-Reduction Mission",
        "description": "Initiative to reduce production costs by 12% this quarter.",
        "tags": ["cost-reduction", "mission"],
    },
]

NOVA_RELATIONSHIPS = [
    {
        "id": "rel-nova-org-employs",
        "type": "employs",
        "sourceEntityId": "org-nova",
        "targetEntityId": "person-qengineer",
        "weight": 1.0,
    },
    {
        "id": "rel-nova-org-employs-2",
        "type": "employs",
        "sourceEntityId": "org-nova",
        "targetEntityId": "person-scanalyst",
        "weight": 1.0,
    },
    {
        "id": "rel-nova-agent-schedules",
        "type": "schedules",
        "sourceEntityId": "agent-nova1",
        "targetEntityId": "workflow-nova1",
        "weight": 0.9,
    },
    {
        "id": "rel-nova-agent-qc",
        "type": "quality_controls",
        "sourceEntityId": "agent-nova2",
        "targetEntityId": "doc-nova1",
        "weight": 0.95,
    },
    {
        "id": "rel-nova-doc-sop",
        "type": "references",
        "sourceEntityId": "doc-nova1",
        "targetEntityId": "workflow-nova1",
        "weight": 0.9,
    },
    {
        "id": "rel-nova-qc-reports",
        "type": "reports_to",
        "sourceEntityId": "agent-nova2",
        "targetEntityId": "doc-nova2",
        "weight": 0.85,
    },
    {
        "id": "rel-nova-analyst-analyzes",
        "type": "analyzes",
        "sourceEntityId": "person-scanalyst",
        "targetEntityId": "workflow-nova1",
        "weight": 0.9,
    },
    {
        "id": "rel-nova-knowledge-relates",
        "type": "relates_to",
        "sourceEntityId": "knowledge-nova1",
        "targetEntityId": "doc-nova1",
        "weight": 0.95,
    },
    {
        "id": "rel-nova-mission-reduces",
        "type": "reduces",
        "sourceEntityId": "mission-nova1",
        "targetEntityId": "org-nova",
        "weight": 1.0,
    },
    {
        "id": "rel-nova-engineer-responsible",
        "type": "responsible_for",
        "sourceEntityId": "person-qengineer",
        "targetEntityId": "doc-nova1",
        "weight": 0.95,
    },
]


# ── Meridian Health Services ─────────────────────────────────────────

MERIDIAN_ENTITIES = [
    {
        "id": "org-meridian",
        "type": "organization",
        "name": "Meridian Health Services",
        "description": "Providing comprehensive healthcare services to the community.",
        "tags": ["healthcare", "clinical", "services"],
    },
    {
        "id": "person-ccoordinator",
        "type": "person",
        "name": "Clinical Coordinator",
        "description": "Coordinates patient care plans and clinical operations.",
        "tags": ["coordinator", "clinical"],
    },
    {
        "id": "person-compliance",
        "type": "person",
        "name": "Compliance Officer",
        "description": "Ensures regulatory compliance and policy adherence.",
        "tags": ["compliance", "officer"],
    },
    {
        "id": "person-omager",
        "type": "person",
        "name": "Operations Manager",
        "description": "Manages daily operations and resource allocation.",
        "tags": ["manager", "operations"],
    },
    {
        "id": "agent-meridian1",
        "type": "agent",
        "name": "Care Plan Agent",
        "description": "Manages patient care plan creation and updates.",
        "tags": ["care-plan", "agent"],
    },
    {
        "id": "agent-meridian2",
        "type": "agent",
        "name": "Audit Agent",
        "description": "Conducts compliance audits and risk assessments.",
        "tags": ["audit", "compliance"],
    },
    {
        "id": "doc-meridian1",
        "type": "document",
        "name": "Care Plan Template",
        "description": "Standard template for patient care plans.",
        "tags": ["template", "care-plan"],
    },
    {
        "id": "doc-meridian2",
        "type": "document",
        "name": "Privacy Policy",
        "description": "Healthcare privacy policy following HIPAA regulations.",
        "tags": ["policy", "privacy", "hipaa"],
    },
    {
        "id": "knowledge-meridian1",
        "type": "knowledge",
        "name": "Patient Safety Knowledge Base",
        "description": "Curated knowledge for patient safety and quality improvement.",
        "tags": ["patient-safety", "knowledge-base"],
    },
    {
        "id": "workflow-meridian1",
        "type": "workflow",
        "name": "Compliance Audit Workflow",
        "description": "End-to-end compliance audit and reporting process.",
        "tags": ["compliance", "workflow"],
    },
    {
        "id": "mission-meridian1",
        "type": "mission",
        "name": "Patient-Safety Mission",
        "description": "Initiative to reduce patient safety incidents by 15% this year.",
        "tags": ["patient-safety", "mission"],
    },
]

MERIDIAN_RELATIONSHIPS = [
    {
        "id": "rel-meridian-org-employs",
        "type": "employs",
        "sourceEntityId": "org-meridian",
        "targetEntityId": "person-ccoordinator",
        "weight": 1.0,
    },
    {
        "id": "rel-meridian-org-employs-2",
        "type": "employs",
        "sourceEntityId": "org-meridian",
        "targetEntityId": "person-compliance",
        "weight": 1.0,
    },
    {
        "id": "rel-meridian-org-employs-3",
        "type": "employs",
        "sourceEntityId": "org-meridian",
        "targetEntityId": "person-omager",
        "weight": 1.0,
    },
    {
        "id": "rel-meridian-agent-manages-care",
        "type": "manages_care",
        "sourceEntityId": "agent-meridian1",
        "targetEntityId": "workflow-meridian1",
        "weight": 0.9,
    },
    {
        "id": "rel-meridian-agent-audits",
        "type": "conducts_audit",
        "sourceEntityId": "agent-meridian2",
        "targetEntityId": "workflow-meridian1",
        "weight": 0.95,
    },
    {
        "id": "rel-meridian-care-uses-template",
        "type": "uses",
        "sourceEntityId": "doc-meridian1",
        "targetEntityId": "agent-meridian1",
        "weight": 0.95,
    },
    {
        "id": "rel-meridian-audit-checks-policy",
        "type": "checks",
        "sourceEntityId": "agent-meridian2",
        "targetEntityId": "doc-meridian2",
        "weight": 0.9,
    },
    {
        "id": "rel-meridian-coordinator-oversees",
        "type": "oversees",
        "sourceEntityId": "person-ccoordinator",
        "targetEntityId": "agent-meridian1",
        "weight": 0.95,
    },
    {
        "id": "rel-meridian-knowledge-relates",
        "type": "relates_to",
        "sourceEntityId": "knowledge-meridian1",
        "targetEntityId": "doc-meridian1",
        "weight": 0.95,
    },
    {
        "id": "rel-meridian-mission-improves",
        "type": "improves",
        "sourceEntityId": "mission-meridian1",
        "targetEntityId": "org-meridian",
        "weight": 1.0,
    },
    {
        "id": "rel-meridian-compliance-regulates",
        "type": "regulates",
        "sourceEntityId": "person-compliance",
        "targetEntityId": "doc-meridian2",
        "weight": 0.95,
    },
]


# ── Enterprise definitions ────────────────────────────────────────────

ENTERPRISES = {
    "apex": {
        "name": "Apex Advisory Group",
        "entities": APEX_ENTITIES,
        "relationships": APEX_RELATIONSHIPS,
        "tenant_id": "apex-advisory-group",
    },
    "nova": {
        "name": "Nova Manufacturing Systems",
        "entities": NOVA_ENTITIES,
        "relationships": NOVA_RELATIONSHIPS,
        "tenant_id": "nova-manufacturing-systems",
    },
    "meridian": {
        "name": "Meridian Health Services",
        "entities": MERIDIAN_ENTITIES,
        "relationships": MERIDIAN_RELATIONSHIPS,
        "tenant_id": "meridian-health-services",
    },
}


# ── API helper ───────────────────────────────────────────────────────

class ApiClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url, timeout=30.0, headers={"Authorization": f"Bearer {token}"}
        )

    async def post(self, path: str, json: dict[str, Any]) -> httpx.Response:
        return await self.client.post(f"{self.base_url}{path}", json=json)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self.client.get(f"{self.base_url}{path}", params=params)

    async def close(self) -> None:
        await self.client.aclose()


# ── Seeder ────────────────────────────────────────────────────────────

class KnowledgeGraphSeeder:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url
        self.clients: dict[str, ApiClient] = {}

    async def _login_and_create_client(self, enterprise: str) -> ApiClient:
        creds = LOGIN_CREDENTIALS[enterprise]
        resp = await self._http_post("/auth/login", json=creds)
        resp.raise_for_status()
        data = resp.json()
        token = data["token"]
        print(f"[auth] logged in as {enterprise}: {data['user']['name']}")
        client = ApiClient(self.base_url, token)
        self.clients[enterprise] = client
        return client

    async def _http_post(self, path: str, json: dict[str, Any]) -> httpx.Response:
        http_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return await http_client.post(f"{self.base_url}{path}", json=json)

    async def create_entities(self, enterprise: str, entities: list[dict[str, Any]]) -> list[str]:
        client = self.clients[enterprise]
        created: list[str] = []
        for entity in entities:
            resp = await client.post("/knowledge-graph/entities", json=entity)
            if resp.status_code in (200, 201):
                data = resp.json()
                created.append(data["id"])
                print(f"[graph] created entity {entity['id']}: {data['name']}")
            elif resp.status_code == 409:
                print(f"[graph] entity already exists {entity['id']}")
                created.append(entity["id"])
            else:
                print(f"[graph] failed entity {entity['id']}: {resp.status_code} {resp.text}")
        return created

    async def create_relationships(self, enterprise: str, relationships: list[dict[str, Any]]) -> list[str]:
        client = self.clients[enterprise]
        # Add tenant_id to relationship metadata
        created: list[str] = []
        for rel in relationships:
            rel_with_tenant = dict(rel)
            rel_with_tenant.setdefault("metadata", {})["tenant_id"] = ENTERPRISES[enterprise]["tenant_id"]
            resp = await client.post("/knowledge-graph/relationships", json=rel_with_tenant)
            if resp.status_code in (200, 201):
                data = resp.json()
                created.append(data["id"])
                print(f"[graph] created relationship {data['id']}: {data['type']}")
            elif resp.status_code == 409:
                print(f"[graph] relationship already exists {rel['id']}")
                created.append(rel["id"])
            else:
                print(f"[graph] failed relationship: {resp.status_code} {resp.text}")
        return created

    async def verify_tenant_isolation(self, enterprise: str) -> dict[str, Any]:
        client = self.clients[enterprise]
        # Check entities
        entities_resp = await client.get("/knowledge-graph/entities")
        entities = entities_resp.json() if entities_resp.status_code == 200 else []
        entity_ids = {e["id"] for e in entities}
        
        # Check relationships
        rels_resp = await client.get("/knowledge-graph/relationships")
        relationships = rels_resp.json() if rels_resp.status_code == 200 else []
        rel_ids = {r["id"] for r in relationships}
        
        # Check stats
        stats_resp = await client.get("/knowledge-graph/stats")
        stats = stats_resp.json() if stats_resp.status_code == 200 else {}
        
        # Check cross-tenant: count entities with other tenant's id in metadata
        cross_tenant_count = 0
        other_enterprises = [e for e in ENTERPRISES if e != enterprise]
        for other in other_enterprises:
            other_tenant = ENTERPRISES[other]["tenant_id"]
            for e in entities:
                if e.get("metadata", {}).get("tenant_id") == other_tenant:
                    cross_tenant_count += 1
        
        return {
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "entity_ids": list(entity_ids),
            "rel_ids": list(rel_ids),
            "stats": stats,
            "cross_tenant_entities": cross_tenant_count,
        }

    async def run(self) -> dict[str, dict[str, Any]]:
        # Login and create clients for all enterprises
        for enterprise in ENTERPRISES:
            await self._login_and_create_client(enterprise)
        
        results: dict[str, dict[str, Any]] = {}
        
        for enterprise, config in ENTERPRISES.items():
            print(f"\n{'='*60}")
            print(f"Seeding {config['name']}...")
            print(f"{'='*60}")
            
            # Create entities
            entity_ids = await self.create_entities(enterprise, config["entities"])
            
            # Create relationships
            rel_ids = await self.create_relationships(enterprise, config["relationships"])
            
            # Verify tenant isolation
            verification = await self.verify_tenant_isolation(enterprise)
            results[enterprise] = verification
            
            print(f"\n{config['name']} summary:")
            print(f"  Entities: {verification['entity_count']}")
            print(f"  Relationships: {verification['relationship_count']}")
            print(f"  Cross-tenant entities: {verification['cross_tenant_entities']}")
            print(f"  Entity types: {verification['stats'].get('entityTypeCounts', {})}")
            print(f"  Relationship types: {verification['stats'].get('relationshipTypeCounts', {})}")
        
        # Close all clients
        for client in self.clients.values():
            await client.close()
        
        return results

    async def close(self) -> None:
        for client in self.clients.values():
            await client.close()


# ── Main ─────────────────────────────────────────────────────────────

async def main() -> int:
    seeder = KnowledgeGraphSeeder()
    try:
        results = await seeder.run()
        
        print("\n" + "="*60)
        print("SEEDING COMPLETE")
        print("="*60)
        
        all_ok = True
        for enterprise, result in results.items():
            config = ENTERPRISES[enterprise]
            print(f"\n{config['name']}:")
            print(f"  Entities: {result['entity_count']}")
            print(f"  Relationships: {result['relationship_count']}")
            print(f"  Cross-tenant entities: {result['cross_tenant_entities']}")
            print(f"  Entity IDs: {result['entity_ids'][:3]}")
            print(f"  Relationship IDs: {result['rel_ids'][:3]}")
            print(f"  Stats: {result['stats']}")
            
            # Validation
            if result['entity_count'] < 5:
                print(f"❌ {config['name']} has insufficient entities ({result['entity_count']})")
                all_ok = False
            if result['relationship_count'] < 8:
                print(f"❌ {config['name']} has insufficient relationships ({result['relationship_count']})")
                all_ok = False
            if result['cross_tenant_entities'] > 0:
                print(f"❌ {config['name']} has cross-tenant data leak ({result['cross_tenant_entities']} entities)")
                all_ok = False
        
        return 0 if all_ok else 1
    finally:
        await seeder.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))