# `eaip.ports`

Hexagonal **ports**: the abstract dependencies the platform needs from its
hosting environment. Each port is a structural `Protocol` so that any
compliant implementation may be plugged in.

| Port | Question it answers |
| ---- | ------------------- |
| `ClockPort` | "what time is it (UTC)?" |
| `IdGeneratorPort` | "give me a fresh opaque ID." |
| `SecretProviderPort` | "what is the value of secret `X`?" |

Default adapters live in [`eaip.infrastructure`](../infrastructure/README.md).
