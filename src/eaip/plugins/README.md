# `eaip.plugins`

Third-party extension surface.

| Symbol | Purpose |
| ------ | ------- |
| `PluginManifest` | Static identity & contract version (read without importing plugin code). |
| `Plugin` (Protocol) | `manifest`, `async activate(platform)`, `async deactivate(platform)`. |
| `PluginRegistry` | Tracks installed plugins. |
| `PluginLoader` | Validates contract, installs, activates/deactivates with idempotency. |

The **plugin contract version** is a separate identifier from the platform
version. A plugin targeting contract `2.x` cannot be installed on a platform
implementing contract `1.x` — this is checked before any plugin code runs.
