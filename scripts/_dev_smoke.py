"""Developer convenience script — exercise the Foundation end to end.

Run via the "EAIP: build_platform smoke" VS Code launch configuration or:

    PYTHONPATH=src python scripts/_dev_smoke.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make the script runnable from a fresh clone before `pip install -e .`.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from eaip.application import build_platform  # noqa: E402


async def main() -> None:
    platform = build_platform()
    print(f"name    = {platform.name}")
    print(f"version = {platform.version}")
    async with platform:
        report = await platform.health.report()
        print(f"phase   = {platform.phase}")
        print(f"health  = {report.status.value} ({report.message})")
    print(f"phase   = {platform.phase}")


if __name__ == "__main__":
    asyncio.run(main())
