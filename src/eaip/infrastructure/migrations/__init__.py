"""Migration registry — auto-discovers all migration modules."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


def load_all_migrations() -> list[Migration]:
    migrations: list[Migration] = []

    try:
        from eaip.infrastructure.migrations.m001_initial_schema import migration as m001

        migrations.append(m001)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m002_second_brains import migration as m002

        migrations.append(m002)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m003_persistence_foundation import (
            migration as m003,
        )

        migrations.append(m003)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m004_b05_persistence import (
            migration as m004,
        )

        migrations.append(m004)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m005_b06_foundations import (
            migration as m005,
        )

        migrations.append(m005)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m006_b07_foundations import (
            migration as m006,
        )

        migrations.append(m006)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m007_scheduling import migration as m007

        migrations.append(m007)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m008_workforce_persistence import (
            migration as m008,
        )

        migrations.append(m008)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m009_simulation import migration as m009

        migrations.append(m009)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m010_marketplace_persistence import (
            migration as m010,
        )

        migrations.append(m010)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m011_mcp_fabric import migration as m011

        migrations.append(m011)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m012_solution_packs import migration as m012

        migrations.append(m012)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m013_swarm_longmissions import migration as m013

        migrations.append(m013)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m014_enterprise_scale import migration as m014

        migrations.append(m014)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m015_wave1_intelligence import migration as m015

        migrations.append(m015)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m016_wave2_application_layer import migration as m016

        migrations.append(m016)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m017_wave3_autonomy_trust import migration as m017

        migrations.append(m017)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m018_m1_memory_knowledge import migration as m018

        migrations.append(m018)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m019_m2_m3_intelligence_reliability import migration as m019

        migrations.append(m019)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m020_strategy_foundation import migration as m020

        migrations.append(m020)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m021_learning_audit_governance import migration as m021

        migrations.append(m021)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m020_learning_audit_governance import migration as m020b

        migrations.append(m020b)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m022_connectors_model_fabric import migration as m022

        migrations.append(m022)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m021_m7_marketplace_deployment import migration as m021

        migrations.append(m021)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m022_m8_scale_ops import migration as m022b

        migrations.append(m022b)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m023_m9_executive import migration as m023

        migrations.append(m023)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m024_m10_loop import migration as m024

        migrations.append(m024)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from eaip.infrastructure.migrations.m025_m2_persistence import migration as m025

        migrations.append(m025)
    except (ImportError, ModuleNotFoundError):
        pass

    migrations.sort(key=lambda m: m.id)
    return migrations


__all__ = ["load_all_migrations"]
