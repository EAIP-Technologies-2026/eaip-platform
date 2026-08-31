"""M4 Synthetic Data — pre-populates strategy data for Apex, Nova, Meridian."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from eaip.shared.time import utc_now
from eaip.strategy.engine import StrategicFrameworkEngine


async def seed_apex_strategy(engine: StrategicFrameworkEngine) -> None:
    """Apex Consulting: consulting strategy objectives, client initiatives, methodology decisions."""
    tenant_id = "apex"
    now = utc_now()

    obj1 = await engine.create_objective(tenant_id, "Expand AI consulting practice", "Grow AI/ML consulting revenue by 40% through new client acquisition and methodology innovation", "high", "sarah.chen", "annual", now, now + timedelta(days=365))
    obj2 = await engine.create_objective(tenant_id, "Client delivery excellence", "Achieve 95%+ client satisfaction across all active engagements", "critical", "marcus.johnson", "annual", now, now + timedelta(days=365))
    obj3 = await engine.create_objective(tenant_id, "Knowledge codification", "Codify top 10 consulting methodologies into reusable frameworks", "medium", "priya.patel", "quarterly", now, now + timedelta(days=90))

    await engine.create_initiative(tenant_id, obj1.id, "AI Readiness Assessment Framework", "Standardized assessment for client AI maturity", 75000, "sarah.chen")
    await engine.create_initiative(tenant_id, obj1.id, "Enterprise AI Strategy Playbook", "Repeatable playbook for enterprise AI transformations", 120000, "priya.patel")
    await engine.create_initiative(tenant_id, obj2.id, "Client Success Dashboard", "Real-time engagement health monitoring", 45000, "marcus.johnson")
    await engine.create_initiative(tenant_id, obj3.id, "Methodology Repository", "Centralized knowledge base for consulting frameworks", 30000, "priya.patel")

    await engine.create_constraint(tenant_id, "budget", "Q3 consulting budget capped at $500K", "high", now, now + timedelta(days=180))
    await engine.create_constraint(tenant_id, "compliance", "All client data must remain in tenant boundary", "critical")

    await engine.create_theme(tenant_id, "AI-First Transformation", "Position Apex as the premier AI transformation partner", 0.9)
    await engine.create_theme(tenant_id, "Operational Excellence", "Streamline internal operations to improve margins", 0.7)

    await engine.create_kpi(tenant_id, obj1.id, "New AI engagements", 12.0, 3.0, "improving")
    await engine.create_kpi(tenant_id, obj2.id, "Client satisfaction score", 95.0, 92.0, "stable")
    await engine.create_kpi(tenant_id, obj3.id, "Methodologies codified", 10.0, 2.0, "improving")

    await engine.create_risk(tenant_id, obj1.id, "Key AI talent retention risk", "high", "high", "Competitive compensation packages and career development plans")
    await engine.create_risk(tenant_id, obj2.id, "Client scope creep on fixed-price engagements", "medium", "medium", "Strict change order process with automated tracking")

    await engine.snapshot_state(tenant_id, "Initial Q3 strategy baseline", "sarah.chen")


async def seed_nova_strategy(engine: StrategicFrameworkEngine) -> None:
    """Nova Manufacturing: manufacturing strategy, production initiatives, supplier decisions."""
    tenant_id = "nova"
    now = utc_now()

    obj1 = await engine.create_objective(tenant_id, "Smart factory modernization", "Deploy IoT sensors and AI-driven predictive maintenance across all production lines", "critical", "james.wu", "annual", now, now + timedelta(days=365))
    obj2 = await engine.create_objective(tenant_id, "Supply chain resilience", "Reduce single-source supplier dependency by 60%", "high", "elena.garcia", "annual", now, now + timedelta(days=365))
    obj3 = await engine.create_objective(tenant_id, "Quality zero-defect program", "Achieve <0.1% defect rate across all product lines", "high", "raj.sharma", "quarterly", now, now + timedelta(days=90))

    await engine.create_initiative(tenant_id, obj1.id, "Predictive Maintenance AI", "ML models for equipment failure prediction", 200000, "james.wu")
    await engine.create_initiative(tenant_id, obj1.id, "Digital Twin Pilot", "Digital twin for production line 3", 150000, "james.wu")
    await engine.create_initiative(tenant_id, obj2.id, "Supplier Diversification Program", "Onboard 5 new qualified suppliers per region", 80000, "elena.garcia")
    await engine.create_initiative(tenant_id, obj3.id, "Computer Vision Quality Inspection", "Automated visual inspection using CV models", 110000, "raj.sharma")

    await engine.create_constraint(tenant_id, "safety", "All AI systems must have human override capability", "critical")
    await engine.create_constraint(tenant_id, "budget", "Capital expenditure approval required above $100K", "high")

    await engine.create_theme(tenant_id, "Industry 4.0", "Transform Nova into a fully connected smart manufacturer", 1.0)
    await engine.create_theme(tenant_id, "Sustainability", "Reduce carbon footprint by 30% by 2027", 0.8)

    await engine.create_kpi(tenant_id, obj1.id, "Predictive maintenance accuracy", 90.0, 72.0, "improving")
    await engine.create_kpi(tenant_id, obj2.id, "Single-source supplier ratio", 40.0, 78.0, "declining")
    await engine.create_kpi(tenant_id, obj3.id, "Defect rate", 0.1, 0.35, "improving")

    await engine.create_risk(tenant_id, obj1.id, "Legacy system integration complexity", "high", "medium", "Phased rollout with parallel operation periods")
    await engine.create_risk(tenant_id, obj2.id, "New supplier qualification delays", "medium", "medium", "Pre-qualified supplier pipeline with expedited audit process")

    await engine.snapshot_state(tenant_id, "Q3 manufacturing strategy baseline", "james.wu")


async def seed_meridian_strategy(engine: StrategicFrameworkEngine) -> None:
    """Meridian Operations: operational strategy, policy initiatives, compliance decisions."""
    tenant_id = "meridian"
    now = utc_now()

    obj1 = await engine.create_objective(tenant_id, "Regulatory compliance automation", "Automate 80% of compliance monitoring and reporting workflows", "critical", "diana.okafor", "annual", now, now + timedelta(days=365))
    obj2 = await engine.create_objective(tenant_id, "Operational cost optimization", "Reduce operational costs by 25% through process automation", "high", "kevin.park", "annual", now, now + timedelta(days=365))
    obj3 = await engine.create_objective(tenant_id, "Policy governance framework", "Implement automated policy enforcement across all operations", "high", "diana.okafor", "quarterly", now, now + timedelta(days=90))

    await engine.create_initiative(tenant_id, obj1.id, "Automated Compliance Scanner", "Continuous monitoring of regulatory changes", 90000, "diana.okafor")
    await engine.create_initiative(tenant_id, obj2.id, "Process Mining & Automation", "Identify and automate top 20 operational processes", 130000, "kevin.park")
    await engine.create_initiative(tenant_id, obj3.id, "Policy-as-Code Engine", "Machine-readable policy definitions with automated enforcement", 70000, "diana.okafor")

    await engine.create_constraint(tenant_id, "regulatory", "Must maintain SOC2 Type II compliance at all times", "critical")
    await engine.create_constraint(tenant_id, "data_residency", "All operational data must remain in primary region", "high")

    await engine.create_theme(tenant_id, "Automated Governance", "Shift from manual to automated policy enforcement", 1.0)
    await engine.create_theme(tenant_id, "Cost Discipline", "Systematic approach to operational efficiency", 0.85)

    await engine.create_kpi(tenant_id, obj1.id, "Compliance automation coverage", 80.0, 35.0, "improving")
    await engine.create_kpi(tenant_id, obj2.id, "Cost reduction achieved", 25.0, 8.0, "improving")
    await engine.create_kpi(tenant_id, obj3.id, "Policies codified", 50.0, 12.0, "improving")

    await engine.create_risk(tenant_id, obj1.id, "Regulatory change velocity exceeds automation pace", "medium", "high", "Dedicated regulatory change monitoring team with 48h response SLA")
    await engine.create_risk(tenant_id, obj3.id, "Policy conflicts between automated rules", "low", "high", "Conflict detection engine with human-in-the-loop resolution")

    await engine.snapshot_state(tenant_id, "Q3 operations strategy baseline", "diana.okafor")


async def seed_all_strategies(engine: StrategicFrameworkEngine) -> None:
    """Seed strategy data for all demo tenants."""
    await seed_apex_strategy(engine)
    await seed_nova_strategy(engine)
    await seed_meridian_strategy(engine)


__all__ = ["seed_all_strategies", "seed_apex_strategy", "seed_meridian_strategy", "seed_nova_strategy"]
