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

    migrations.sort(key=lambda m: m.id)
    return migrations


__all__ = ["load_all_migrations"]
