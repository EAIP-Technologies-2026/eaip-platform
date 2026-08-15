# `eaip.application`

Convenience entry points for hosts.

| Function | Purpose |
| -------- | ------- |
| `build_platform(...)` | One-line construction with sensible defaults. |
| `run_platform(platform, on_running=...)` | Install signal handlers, start, await shutdown, stop. |

```python
import asyncio
from eaip.application import build_platform, run_platform


async def main() -> None:
    platform = build_platform()
    await run_platform(platform)


asyncio.run(main())
```

The async runner installs `SIGINT` / `SIGTERM` handlers, runs an optional
`on_running` callback, blocks until a shutdown signal arrives, and *always*
stops the platform cleanly — even if the callback raises.
