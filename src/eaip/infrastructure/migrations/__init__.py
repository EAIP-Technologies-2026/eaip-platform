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

    migrations.sort(key=lambda m: m.id)
    return migrations


__all__ = ["load_all_migrations"]
