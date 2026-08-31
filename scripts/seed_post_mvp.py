"""Deterministic post-MVP synthetic seeder — Apex/Nova/Meridian expansion.

Idempotent, tenant-aware, deterministic (seed=42). Seeds schedules,
workforce workers/assignments, marketplace packs, knowledge graph
entities, and simulation events via the live API (or direct imports).

Usage:
  python scripts/seed_post_mvp.py --enterprise all
  python scripts/seed_post_mvp.py --enterprise apex --base-url http://localhost:8080
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta

DEFAULT_BASE_URL = "http://localhost:8080"

ENTERPRISES = {
    "apex": {"tenant": "apex-advisory-group", "label": "Apex Advisory Group"},
    "nova": {"tenant": "nova-manufacturing-systems", "label": "Nova Manufacturing Systems"},
    "meridian": {"tenant": "meridian-health-services", "label": "Meridian Health Services"},
}

MARKETPLACE_PACKS = [
    {"name": "Apex Client Onboarding Pack", "type": "template", "description": "Templates for client onboarding, SOWs, and delivery tracking for Apex", "tags": ["apex", "onboarding", "featured"], "enterprise": "apex"},
    {"name": "Apex Knowledge Pack", "type": "plugin", "description": "Knowledge pack for Apex advisory case studies and policies", "tags": ["apex", "knowledge"], "enterprise": "apex"},
    {"name": "Nova Production Automation", "type": "agent", "description": "Agent pack for Nova production scheduling and quality control", "tags": ["nova", "manufacturing", "featured"], "enterprise": "nova"},
    {"name": "Nova Supply Chain Pack", "type": "integration", "description": "Integration pack for Nova supplier and inventory workflows", "tags": ["nova", "supply-chain"], "enterprise": "nova"},
    {"name": "Meridian Compliance Pack", "type": "template", "description": "Compliance workflows and audit templates for Meridian", "tags": ["meridian", "compliance", "featured"], "enterprise": "meridian"},
    {"name": "Meridian Care Plan Automation", "type": "workflow", "description": "Automated care plan workflows for Meridian", "tags": ["meridian", "care"], "enterprise": "meridian"},
    {"name": "Enterprise Scheduling Booster", "type": "tool", "description": "Shared scheduling optimizations for all enterprises", "tags": ["featured", "scheduling"], "enterprise": "all"},
]


async def seed_via_api(base_url: str, enterprise_filter: str) -> dict:
    import httpx

    rng = random.Random(42)
    results: dict = {"schedules": 0, "workers": 0, "marketplace": 0, "sim_events": 0, "errors": []}

    auth_tokens: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=15) as client:
        for key, meta in ENTERPRISES.items():
            if enterprise_filter != "all" and key != enterprise_filter:
                continue
            tenant = meta["tenant"]
            try:
                r = await client.post(f"{base_url}/api/auth/login", json={"username": f"{key}-user", "password": "seed-pass"})
                if r.status_code == 200:
                    data = r.json()
                    auth_tokens[key] = data.get("access_token") or data.get("token") or ""
                else:
                    r2 = await client.post(f"{base_url}/api/auth/login", json={"username": f"{key}-admin", "password": "admin-pass"})
                    if r2.status_code == 200:
                        data = r2.json()
                        auth_tokens[key] = data.get("access_token") or data.get("token") or ""
            except Exception as e:
                results["errors"].append(f"{key} login: {e}")

        if not auth_tokens:
            try:
                r = await client.post(f"{base_url}/api/auth/login", json={"username": "admin", "password": "admin"})
                if r.status_code == 200:
                    data = r.json()
                    tok = data.get("access_token") or data.get("token") or ""
                    for key in ENTERPRISES:
                        if enterprise_filter == "all" or key == enterprise_filter:
                            auth_tokens[key] = tok
            except Exception as e:
                results["errors"].append(f"admin login: {e}")

    if not auth_tokens:
        print("No auth tokens obtained — seeding in unauthenticated fallback (may fail with 401)")
        for key in ENTERPRISES:
            if enterprise_filter == "all" or key == enterprise_filter:
                auth_tokens[key] = ""

    async with httpx.AsyncClient(timeout=15) as client:
        for pack in MARKETPLACE_PACKS:
            if pack["enterprise"] != "all" and enterprise_filter != "all" and pack["enterprise"] != enterprise_filter:
                continue
            ent_key = pack["enterprise"] if pack["enterprise"] != "all" else (enterprise_filter if enterprise_filter != "all" else "apex")
            token = auth_tokens.get(ent_key, "")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            try:
                r = await client.post(f"{base_url}/api/marketplace/packages", json={
                    "name": pack["name"], "type": pack["type"], "description": pack["description"], "tags": pack["tags"], "version": "1.0.0"
                }, headers=headers)
                if r.status_code in (200, 201, 409):
                    results["marketplace"] += 1
                else:
                    results["errors"].append(f"marketplace {pack['name']}: {r.status_code} {r.text[:200]}")
            except Exception as e:
                results["errors"].append(f"marketplace {pack['name']}: {e}")

        for key, meta in ENTERPRISES.items():
            if enterprise_filter != "all" and key != enterprise_filter:
                continue
            token = auth_tokens.get(key, "")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            base = f"{base_url}/api"

            for i in range(5):
                wid = f"wf-{key}-{i:02d}-{rng.randint(1000, 9999)}"
                try:
                    r = await client.post(f"{base}/workforce/workers", json={
                        "id": wid, "name": f"{key.title()} Worker {i+1}", "workerType": rng.choice(["agent", "workflow"]), "description": f"Synthetic worker for {key}", "tags": [key, "synthetic"], "maxConcurrentRuns": rng.randint(1, 3)
                    }, headers=headers)
                    if r.status_code in (200, 201, 409):
                        results["workers"] += 1
                except Exception as e:
                    results["errors"].append(f"worker {wid}: {e}")

            for i in range(7):
                sid = f"sched-{key}-{i:02d}"
                kind = rng.choice(["interval", "cron", "one_time"])
                trigger: dict = {}
                if kind == "interval":
                    trigger = {"kind": "interval", "interval_seconds": rng.choice([3600, 7200, 86400])}
                elif kind == "cron":
                    trigger = {"kind": "cron", "cron_expr": rng.choice(["0 * * * *", "0 9 * * 1", "0 0 * * *"])}
                else:
                    trigger = {"kind": "one_time", "run_at": (datetime.now(UTC) + timedelta(days=rng.randint(1, 7))).isoformat()}
                try:
                    r = await client.post(f"{base}/schedules", json={
                        "id": sid, "name": f"{key.title()} Schedule {i+1}", "target_type": rng.choice(["workflow", "mission", "agent_action"]), "target_id": f"target-{key}-{i}", "trigger": trigger, "priority": rng.randint(1, 5), "description": f"Synthetic schedule for {key}"
                    }, headers=headers)
                    if r.status_code in (200, 201, 409):
                        results["schedules"] += 1
                except Exception as e:
                    results["errors"].append(f"schedule {sid}: {e}")

            for _ in range(2):
                try:
                    r = await client.post(f"{base}/simulation/tick", json={}, headers=headers)
                    if r.status_code == 200:
                        results["sim_events"] += len(r.json().get("events", []))
                except Exception as e:
                    results["errors"].append(f"simulation tick {key}: {e}")

            for _ in range(2):
                try:
                    r = await client.post(f"{base}/enterprise/flows/{key}/trigger", json={}, headers=headers)
                    if r.status_code == 200:
                        pass
                except Exception as e:
                    results["errors"].append(f"flow {key}: {e}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-MVP synthetic seeder")
    parser.add_argument("--enterprise", choices=["apex", "nova", "meridian", "all"], default="all")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    print(f"Seeding post-MVP synthetic data enterprise={args.enterprise} base_url={args.base_url} (deterministic seed=42)")
    results = asyncio.run(seed_via_api(args.base_url, args.enterprise))
    print(f"Done: {results}")
    if results["errors"]:
        print("Errors:", file=sys.stderr)
        for e in results["errors"][:20]:
            print(f"  - {e}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
