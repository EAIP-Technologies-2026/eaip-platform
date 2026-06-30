# `eaip.infrastructure`

Default, dependency-free implementations of every port the Foundation
declares.

| Port | Default adapter | Notes |
| ---- | --------------- | ----- |
| `ClockPort` | `SystemClock` | UTC `datetime.now`. |
| `IdGeneratorPort` | `UuidIdGenerator` | UUIDv4 strings. |
| `SecretProviderPort` | `EnvSecretProvider` | Reads `os.environ`. |

Hosts swap any of these via the DI container; the rest of the platform
depends only on the **port**, never on these defaults.
