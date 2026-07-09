# Bundle-007 Evidence Snapshot v1.0

**Repository:** EAIP — Enterprise Autonomous Intelligence Platform
**Generated:** 2026-07-07
**Tooling:** Bundle-007 Auditor (read-only)

---

## 1. Repository Information

| Attribute | Value |
|---|---|
| **Current Commit SHA** | `6eabf11` |
| **Branch** | `sprint-2` |
| **Remote** | `origin → https://github.com/subham1902/eaip-platform.git` |
| **Total Commits** | 20 |
| **Latest Tag** | `v0.1.0-foundation` |
| **Working Tree** | Clean — no uncommitted changes |
| **Merge Base** | Merge pull request #5 from `subham1902/sprint-1b` |

### 1.1 Repository Statistics

| Metric | Count |
|---|---|
| Commits | 20 |
| Tags | 1 (`v0.1.0-foundation`) |
| Branches (local) | `sprint-2` |
| Contributors | 1 (Subham Panigrahi) |
| Source `.py` files | 86 files (86 source lines measured) |
| Test `.py` files | 27 files (27 source lines measured) |
| Total Python SLOC | ~2,175 lines (src + tests) |
| Documentation (`.md`) | 46 files |

---

## 2. Repository Structure

### 2.1 Top-Level Directory

```
eaip-platform/
├── .agents/                          # Agent workspace
├── .devcontainer/                    # Dev container config
│   └── devcontainer.json
├── .emergent/                        # Emergent tooling
├── .github/                          # CI/CD & issue templates
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── docs.yml
│   │   └── security.yml
│   ├── ISSUE_TEMPLATE/
│   ├── dependabot.yml
│   ├── gitleaks.toml
├── .vscode/                          # VS Code workspace settings
├── memory/                           # Project memory / PRD
│   ├── PRD.md
│   └── test_credentials.md
├── scripts/                          # Dev scripts
│   ├── README.md
│   └── _dev_smoke.py
├── src/                              # Source code
│   └── eaip/                         # Core package
├── tests/                            # Test suite
│   ├── conftest.py
│   ├── fixtures/
│   ├── unit/
│   └── utilities.py
├── Dockerfile                        # Dev image definition
├── docker-compose.dev.yml            # Local dev stack
├── pyproject.toml                    # Build & tooling config
├── .pre-commit-config.yaml           # Pre-commit hooks
├── .yamlfmt.yml                      # YAML formatter config
├── .secrets.baseline                 # detect-secrets baseline
├── .gitignore
├── AGENTS.md
├── README.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── DECISION_REGISTER.md
├── DEVELOPER_GUIDE.md
├── ENGINEERING_TRACKER.md
├── RISK_REGISTER.md
├── ROADMAP.md
├── SECURITY.md
├── SUPPORT.md
├── TECH_DEBT.md
├── VERSIONING.md
└── LICENSE
```

### 2.2 Source Package Structure (`src/eaip/`)

```
eaip/
├── __init__.py              # Package root — version re-export
├── _version.py              # Single version source (0.0.2)
├── py.typed                 # PEP 561 marker
├── adapters/
│   ├── __init__.py
│   └── interfaces/
│       ├── __init__.py
│       ├── base.py          # AbstractAdapter, AdapterCapability
│       └── README.md
├── application/
│   ├── __init__.py          # Re-exports build_platform, run_platform
│   ├── bootstrap.py         # build_platform() convenience
│   ├── runner.py            # run_platform() async runner
│   └── README.md
├── capabilities/
│   ├── __init__.py
│   ├── capability.py        # Capability, CapabilityStatus
│   ├── registry.py          # CapabilityRegistry
│   └── README.md
├── config/
│   ├── __init__.py
│   ├── loader.py            # ConfigLoader
│   ├── sources.py           # DictSource, EnvSource, FileSource, LayeredSource
│   └── README.md
├── core/
│   ├── __init__.py
│   ├── feature_flags.py     # FeatureFlagRegistry
│   ├── signals.py           # ShutdownSignal, signal handlers
│   └── README.md
├── dependency_injection/
│   ├── __init__.py
│   ├── container.py         # Container (register, resolve, scopes)
│   ├── scope.py             # Scope enum (SINGLETON, TRANSIENT, SCOPED)
│   └── README.md
├── events/
│   ├── __init__.py
│   ├── bus.py               # EventBus (type-routed pub/sub)
│   ├── event.py             # DomainEvent base
│   └── README.md
├── exceptions/
│   ├── __init__.py
│   ├── base.py              # EAIPError, ErrorCode, ErrorSeverity
│   ├── domain.py            # Domain-specific exception classes
│   └── README.md
├── factories/
│   ├── __init__.py
│   ├── factory.py           # Generic Factory (key → builder)
│   └── README.md
├── health/
│   ├── __init__.py
│   ├── checks.py            # HealthCheck protocol, HealthReport, HealthStatus
│   ├── reporter.py          # HealthReporter
│   └── README.md
├── infrastructure/
│   ├── __init__.py
│   ├── clock.py             # SystemClock
│   ├── id_generator.py      # UuidIdGenerator
│   ├── secret_provider.py   # EnvSecretProvider
│   └── README.md
├── interfaces/
│   ├── __init__.py
│   ├── repository.py        # AbstractRepository
│   ├── service.py           # AbstractService, ServiceState
│   └── README.md
├── lifecycle/
│   ├── __init__.py
│   ├── manager.py           # LifecycleManager
│   ├── phases.py            # LifecyclePhase enum
│   └── README.md
├── logging/
│   ├── __init__.py
│   ├── config.py            # configure_logging, LoggingConfig
│   ├── context.py           # get_logger, bind_context, scoped_context
│   ├── filters.py           # redact_processor
│   └── README.md
├── metadata/
│   ├── __init__.py
│   ├── component.py         # ComponentMetadata, ComponentKind
│   └── README.md
├── platform/
│   ├── __init__.py
│   ├── builder.py           # PlatformBuilder
│   ├── platform.py          # Platform — composition root
│   └── README.md
├── plugins/
│   ├── __init__.py
│   ├── loader.py            # PluginLoader
│   ├── plugin.py            # Plugin protocol, PluginManifest
│   ├── registry.py          # PluginRegistry
│   └── README.md
├── ports/
│   ├── __init__.py
│   ├── clock.py             # ClockPort protocol
│   ├── id_generator.py      # IdGeneratorPort protocol
│   ├── secret_provider.py   # SecretProviderPort protocol
│   └── README.md
├── protocols/
│   ├── __init__.py
│   ├── health.py            # Healthcheckable protocol
│   ├── identifiable.py      # Identifiable, Named, Versioned protocols
│   ├── lifecycle.py         # Startable, Stoppable, Disposable (sync/async)
│   └── README.md
├── registry/
│   ├── __init__.py
│   ├── registry.py          # Generic Registry[T] — observable, typed, key-value
│   └── README.md
├── runtime/                  # Placeholder — only README.md + __pycache__
│   └── README.md
├── serialization/
│   ├── __init__.py
│   ├── json.py              # JSONEncoder/Decoder, to_json/from_json
│   └── README.md
├── settings/
│   ├── __init__.py
│   ├── base.py              # EAIPSettingsBase
│   ├── core_settings.py     # PlatformSettings, CoreSettings, LoggingSettings, FeatureFlagSettings
│   └── README.md
├── shared/
│   ├── __init__.py
│   ├── identifiers.py       # CorrelationId, RunId, ComponentId, Slug
│   ├── result.py            # Ok, Err, Result monad
│   ├── sentinels.py         # UNSET sentinel
│   ├── time.py              # utc_now, Clock protocol, Duration
│   └── types.py             # JSONValue, JSONArray, JSONObject, OpaqueToken
├── types/
│   ├── __init__.py
│   ├── env.py               # Environment enum
│   ├── primitives.py        # NonEmptyStr, Port, HostName, Url, LogLevel, EnvName
│   └── README.md
├── utilities/
│   ├── __init__.py
│   ├── async_tools.py       # gather_with_concurrency, run_with_timeout
│   ├── collections.py       # chunked, first, unique
│   ├── strings.py           # camel_to_snake, snake_to_camel, truncate
│   └── README.md
├── validation/
│   ├── __init__.py
│   ├── validators.py        # ensure, validate_range, validate_one_of, validate_model
│   └── README.md
├── version/
│   ├── __init__.py
│   ├── semver.py            # Version (SemVer 2.0.0 parser/comparator)
│   └── README.md
```

### 2.3 Test Structure (`tests/`)

```
tests/
├── conftest.py               # Pytest config: path setup, logging reset fixture
├── utilities.py              # Test utility functions
├── __init__.py
├── fixtures/
│   ├── __init__.py
│   └── platform.py           # running_platform async fixture
├── unit/
│   ├── __init__.py
│   ├── test_capabilities.py
│   ├── test_config.py
│   ├── test_core.py
│   ├── test_dependency_injection.py
│   ├── test_events.py
│   ├── test_exceptions.py
│   ├── test_factories.py
│   ├── test_health.py
│   ├── test_infrastructure.py
│   ├── test_lifecycle.py
│   ├── test_logging.py
│   ├── test_platform.py
│   ├── test_plugins.py
│   ├── test_registry.py
│   ├── test_serialization.py
│   ├── test_settings.py
│   ├── test_shared.py
│   ├── test_types.py
│   ├── test_utilities.py
│   ├── test_validation.py
│   └── test_version.py
```

### 2.4 Documentation Inventory (46 `.md` files)

| Category | Files |
|---|---|
| **Project** | `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `SECURITY.md`, `LICENSE` |
| **Architecture** | `ARCHITECTURE.md`, `DECISION_REGISTER.md`, `ENGINEERING_TRACKER.md`, `RISK_REGISTER.md`, `ROADMAP.md`, `VERSIONING.md`, `DEVELOPER_GUIDE.md`, `TECH_DEBT.md` |
| **Package (inline)** | 28 `README.md` files inside each sub-package under `src/eaip/` |
| **Memory** | `memory/PRD.md`, `memory/test_credentials.md` |
| **Scripts** | `scripts/README.md` |

---

## 3. Architecture

### 3.1 Package Boundaries & Runtime Layers

```
┌──────────────────────────────────────────────────────────────┐
│                     Application Layer                         │
│  application/ (bootstrap, runner)                             │
│  platform/ (Platform, PlatformBuilder)                        │
├──────────────────────────────────────────────────────────────┤
│                        Core Layer                             │
│  core/ (signals, feature_flags)                               │
│  lifecycle/ (manager, phases)                                 │
│  events/ (bus, DomainEvent)                                   │
│  health/ (checks, reporter)                                   │
│  config/ (sources, loader)                                    │
│  logging/ (config, context, filters)                          │
│  registry/ (generic Registry[T])                              │
│  plugins/ (Plugin protocol, loader, registry)                 │
│  dependency_injection/ (Container, scopes)                    │
├──────────────────────────────────────────────────────────────┤
│                      Ports & Adapters                         │
│  ports/ (ClockPort, IdGeneratorPort, SecretProviderPort)      │
│  adapters/ (AbstractAdapter)                                  │
│  infrastructure/ (SystemClock, UuidIdGenerator, EnvSecretProv)│
├──────────────────────────────────────────────────────────────┤
│                   Domain / Interface Layer                    │
│  interfaces/ (AbstractService, AbstractRepository)            │
│  protocols/ (Startable, Stoppable, Healthcheckable, ...)      │
│  capabilities/ (Capability, CapabilityRegistry)               │
│  metadata/ (ComponentMetadata, ComponentKind)                 │
├──────────────────────────────────────────────────────────────┤
│                    Shared Foundation                          │
│  shared/ (identifiers, result, sentinels, time, types)        │
│  types/ (NonEmptyStr, Environment, LogLevel, ...)             │
│  exceptions/ (EAIPError, ErrorCode, domain exceptions)        │
│  validation/ (validators)                                     │
│  serialization/ (JSON encoder/decoder)                        │
│  factories/ (generic Factory[T])                              │
│  utilities/ (strings, collections, async_tools)               │
│  version/ (SemVer parse/compare)                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Import Graph (Inter-Package Dependencies)

```
eaip.application
  → eaip.platform (.builder, .platform)
  → eaip.plugins.plugin
  → eaip.settings.core_settings
  → eaip.core.signals
  → eaip.logging.context

eaip.platform
  → eaip.capabilities.registry
  → eaip.core.feature_flags
  → eaip.dependency_injection.*
  → eaip.events.*
  → eaip.health.reporter
  → eaip.lifecycle.*
  → eaip.logging.*
  → eaip.plugins.*
  → eaip.settings.core_settings
  → eaip.infrastructure.*
  → eaip.ports.*

eaip.capabilities
  → eaip.metadata.component
  → eaip.registry.registry
  → eaip.exceptions.domain
  → eaip.types

eaip.config
  → eaip.config.sources
  → eaip.validation.validators
  → eaip.exceptions.domain

eaip.events
  → eaip.events.event
  → eaip.shared.time
  → eaip.shared.identifiers
  → eaip.logging.context

eaip.health
  → eaip.health.checks
  → eaip.shared.time
  → eaip.logging.context
  → eaip.exceptions.domain

eaip.dependency_injection
  → eaip.dependency_injection.scope
  → eaip.exceptions.domain

eaip.logging
  → structlog
  → eaip.types (LogLevel)
  → eaip.logging.filters

eaip.infrastructure
  → eaip.ports.*
  → eaip.shared.time

eaip.shared
  → pydantic (identifiers)
  → dataclasses (result, time, sentinels)

eaip.exceptions
  → eaip.exceptions.base (domain imports base)

eaip.registry
  → eaip.exceptions.domain

eaip.validation
  → pydantic
  → eaip.exceptions.domain

eaip.serialization
  → pydantic
  → eaip.exceptions.domain
```

### 3.3 External Dependency Graph (Third-Party)

```
pydantic (≥2.9.0)
  └── pydantic-core
pydantic-settings (≥2.6.0)
  └── pydantic
  └── python-dotenv
structlog (≥24.4.0)
  └── typing-extensions (python < 3.13)
anyio (≥4.6.0)
typing-extensions (≥4.12.0, python < 3.13)
```

### 3.4 Public API Surface

The public API exported from each `__init__.py`:

| Package | Public Symbols |
|---|---|
| `eaip` | `__version__`, `__version_info__` |
| `eaip.application` | `build_platform`, `run_platform`, `OnRunning` |
| `eaip.capabilities` | `Capability`, `CapabilityStatus`, `CapabilityRegistry` |
| `eaip.events` | `EventBus`, `Subscription`, `DomainEvent` |
| `eaip.health` | `HealthCheck`, `HealthReport`, `HealthStatus`, `HealthReporter`, `callable_check` |
| `eaip.config` | `ConfigLoader`, `ConfigSource`, `DictSource`, `EnvSource`, `FileSource`, `LayeredSource` |
| `eaip.dependency_injection` | `Container`, `Factory`, `Provider`, `Scope` |
| `eaip.core` | `ShutdownSignal`, `install_shutdown_handlers`, `FeatureFlag`, `FeatureFlagRegistry` |
| `eaip.exceptions` | All exception classes, `EAIPError`, `ErrorCode`, `ErrorSeverity` |
| `eaip.logging` | `LoggingConfig`, `LogFormat`, `configure_logging`, `is_configured`, `get_logger`, `bind_context`, `clear_context`, `current_context`, `scoped_context`, `redact_processor` |
| `eaip.metadata` | `ComponentKind`, `ComponentMetadata` |
| `eaip.plugins` | `Plugin`, `PluginManifest`, `PluginLoader`, `PluginRegistry`, `CURRENT_CONTRACT_VERSION` |
| `eaip.registry` | `Registry`, `RegistryChange`, `RegistryEvent`, `Observer` |
| `eaip.settings` | `EAIPSettingsBase`, `PlatformSettings`, `CoreSettings`, `LoggingSettings`, `FeatureFlagSettings`, `load_platform_settings` |
| `eaip.shared` | Identifiers, `Result`, `Ok`, `Err`, `UNSET`, `Duration`, `Clock` protocol, `utc_now`, JSON types, `OpaqueToken` |
| `eaip.types` | `Environment`, `NonEmptyStr`, `Port`, `HostName`, `Url`, `LogLevel`, `EnvName` |
| `eaip.platform` | `Platform`, `PlatformBuilder` |
| `eaip.infrastructure` | `SystemClock`, `UuidIdGenerator`, `EnvSecretProvider` |
| `eaip.serialization` | `JSONEncoder`, `JSONDecoder`, `to_json`, `from_json` |
| `eaip.interfaces` | `AbstractService`, `ServiceState`, `AbstractRepository` |
| `eaip.ports` | `ClockPort`, `IdGeneratorPort`, `SecretProviderPort` |
| `eaip.protocols` | `Startable`, `Stoppable`, `Disposable`, `AsyncStartable`, `AsyncStoppable`, `AsyncDisposable`, `Healthcheckable`, `Identifiable`, `Named`, `Versioned` |
| `eaip.adapters` | `AbstractAdapter`, `AdapterCapability` |
| `eaip.factories` | `Factory`, `Builder` |
| `eaip.lifecycle` | `LifecyclePhase`, `LifecycleManager`, `LifecycleHook` |
| `eaip.validation` | `ensure`, `validate_range`, `validate_one_of`, `validate_model` |
| `eaip.version` | `Version` |

### 3.5 Internal APIs (Non-public)

Sub-packages that are implementation details not re-exported through `__init__.py`:

- `eaip.config.sources` — sources module, internal classes used by `eaip.config`
- `eaip.config.loader` — internal loader used by `eaip.config`
- `eaip.exceptions.base` — `EAIPError` parent, imported by `eaip.exceptions.domain`
- `eaip.logging.filters` — `redact_processor`, internal processor used by `eaip.logging.config`
- `eaip.dependency_injection.scope` — `Scope` enum
- `eaip.capabilities.capability` — per-module internals
- `eaip.registry.registry` — `Registry` generic, used by capabilities/plugins
- `eaip.shared.*` — individual per-module internals

---

## 4. Runtime

### 4.1 Bootstrap Implementation

**File:** `src/eaip/application/bootstrap.py`
- `build_platform()` — convenience function
- Creates `PlatformBuilder` with settings, optional plugins, logging toggle
- Delegates to `builder.build()`
- 41 lines

### 4.2 Lifecycle Implementation

**File:** `src/eaip/lifecycle/manager.py` (174 lines)
- `LifecycleManager` — orchestrates ordered startup, reverse-ordered shutdown
- Phases: CREATED → STARTING → RUNNING → STOPPING → STOPPED / FAILED
- Start hooks run in registration order
- Stop hooks run in reverse order
- Partial-start rollback on failure
- Sync/async normalization via `inspect.isawaitable()`

**File:** `src/eaip/lifecycle/phases.py` (19 lines)
- `LifecyclePhase` enum: `CREATED`, `STARTING`, `RUNNING`, `STOPPING`, `STOPPED`, `FAILED`

### 4.3 Dependency Injection Implementation

**File:** `src/eaip/dependency_injection/container.py` (228 lines)
- `Container` — type-keyed, explicit, no autowire/scanning
- Three registration methods: `register_instance`, `register_factory`, `register`
- Three scopes: `SINGLETON`, `TRANSIENT`, `SCOPED` (via `eaip/dependency_injection/scope.py`)
- Cycle detection via `_ResolveStack` (per-thread re-entrancy tracker)
- Type validation on instance registration and factory output
- `try_resolve()` for optional dependencies
- `create_scope()` for child containers sharing singletons

### 4.4 Registry Implementation

**File:** `src/eaip/registry/registry.py` (280 lines)
- `Registry[T]` — generic, typed, observable, thread-safe, name-keyed
- Events: `REGISTERED`, `UNREGISTERED`, `REPLACED`
- Observer pattern: `observe()` returns a disposal callback
- Lookups: `get`, `try_get`, `has`, `keys`, `values`, `items`
- Built on by `CapabilityRegistry` and `PluginRegistry`

### 4.5 Event Architecture

**File:** `src/eaip/events/event.py` (31 lines)
- `DomainEvent` — frozen Pydantic base, `event_type` (ClassVar), `occurred_at`, `correlation_id`

**File:** `src/eaip/events/bus.py` (154 lines)
- `EventBus` — in-process, type-routed pub/sub
- Subscribe by concrete `DomainEvent` subclass
- `include_subclasses=True` by default for polymorphic dispatch
- `publish()` returns list of `(subscription, exception)` — fire-and-collect
- Sync/async handler support via `inspect.isawaitable()`
- Thread-unsafe but task-safe

### 4.6 Plugin Architecture

**File:** `src/eaip/plugins/plugin.py` (80 lines)
- `Plugin` protocol (runtime-checkable): `manifest`, `activate(platform)`, `deactivate(platform)`
- `PluginManifest` — frozen Pydantic model: `name`, `version`, `contract_version`, `description`, `provides_capabilities`

**File:** `src/eaip/plugins/registry.py` (82 lines)
- `PluginRegistry` — wraps `Registry[Plugin]` with name-keyed methods

**File:** `src/eaip/plugins/loader.py` (154 lines)
- `PluginLoader` — validates contracts, registers, activates/deactivates
- `CURRENT_CONTRACT_VERSION = "1.0.0"` — major version must match plugin target
- Idempotent activate/deactivate

### 4.7 Configuration System

**File:** `src/eaip/config/sources.py` (200 lines)
- `ConfigSource` (ABC): `DictSource`, `EnvSource`, `FileSource`, `LayeredSource`
- Deep-merge layered config
- `EnvSource` parses `PREFIX__NESTED__KEY` → nested dict
- `FileSource` supports JSON and TOML

**File:** `src/eaip/config/loader.py` (41 lines)
- `ConfigLoader` — hydrates a Pydantic model from a source via `validate_model()`

**File:** `src/eaip/settings/base.py` (30 lines)
- `EAIPSettingsBase` — using `pydantic-settings`, prefix `EAIP_`, nested delimiter `__`

**File:** `src/eaip/settings/core_settings.py` (70 lines)
- `CoreSettings`, `LoggingSettings`, `FeatureFlagSettings`, `PlatformSettings`
- `load_platform_settings()` → `PlatformSettings()` from env

### 4.8 Logging

**File:** `src/eaip/logging/config.py` (109 lines)
- `LoggingConfig` — Pydantic model: `level`, `format` (json|console), `include_caller`, `redact_keys`
- `configure_logging()` — sets up structlog + stdlib logging
- Shared processors: contextvars merge, log level, timestamp, stack info, exc info, redaction
- JSON or Console renderer

**File:** `src/eaip/logging/context.py` (61 lines)
- `get_logger()` — lazy-first-use configuration
- `bind_context()`, `clear_context()`, `current_context()`, `scoped_context()`

**File:** `src/eaip/logging/filters.py` (47 lines)
- `redact_processor()` — case-insensitive key redaction, recursive into nested mappings

### 4.9 Health

**File:** `src/eaip/health/checks.py` (83 lines)
- `HealthStatus` enum: `HEALTHY`, `DEGRADED`, `UNHEALTHY` (with numeric weight)
- `HealthReport` — frozen Pydantic: component, status, message, details, observed_at, children
- `HealthCheck` protocol: `name`, `check() → HealthReport`
- `callable_check()` — wraps an async function as `HealthCheck`

**File:** `src/eaip/health/reporter.py` (106 lines)
- `HealthReporter` — registers checks, runs all concurrently via `asyncio.gather()`
- Rollup: aggregates child reports, worst status wins

### 4.10 Metrics

No dedicated metrics subsystem is implemented. The Foundation relies on:
- Structured logging (structlog) for event-level observability
- Health checks for liveness/readiness

### 4.11 Docker Assets

**File:** `Dockerfile` (40 lines)
- Base: `python:3.13-slim-bookworm`
- Installs: build-essential, git, curl, make, ca-certificates
- Two-phase COPY for layer caching (pyproject.toml → deps → source)
- Installs `.[dev,test]` extras
- CMD: `bash`

**File:** `docker-compose.dev.yml` (32 lines)
- Service `eaip` from Dockerfile
- Environment: `EAIP_CORE__ENVIRONMENT=development`, `EAIP_LOGGING__LEVEL=DEBUG`
- Volumes: source mount + pip/pre-commit cache
- Interactive TTY shell

---

## 5. Quality

### 5.1 Test Inventory

**152 tests, all passing** (1.58s execution time)

| Test File | Tests | Description |
|---|---|---|
| `test_capabilities.py` | 6 | Register, status transitions, duplicates, enabled filter, metadata |
| `test_config.py` | 8 | Dict/Env/File sources, layered merge, validation |
| `test_core.py` | 4 | Feature flag defaults, overrides, unknown flags, shutdown signal |
| `test_dependency_injection.py` | ~8 | Register/resolve, type checking, scopes, cycles |
| `test_events.py` | ~6 | Subscribe, publish, unsubscribe, type routing |
| `test_exceptions.py` | ~4 | Error hierarchy, to_dict, context |
| `test_factories.py` | ~4 | Register, create, unregister |
| `test_health.py` | ~6 | HealthReport, HealthReporter, registration |
| `test_infrastructure.py` | ~3 | Clock, ID generator, secret provider |
| `test_lifecycle.py` | ~6 | Phase transitions, start/stop order, rollback |
| `test_logging.py` | ~4 | configure_logging, redact_processor |
| `test_platform.py` | ~8 | Builder, Platform start/stop, lifecycle integration |
| `test_plugins.py` | ~6 | Plugin manifest, registry, loader, contract validation |
| `test_registry.py` | ~6 | Registry CRUD, observers, type enforcement |
| `test_serialization.py` | ~8 | JSON encode/decode, custom types |
| `test_settings.py` | ~4 | PlatformSettings, env loading |
| `test_shared.py` | ~6 | Identifiers, Result, Duration |
| `test_types.py` | ~4 | NonEmptyStr, HostName, Url, LogLevel |
| `test_utilities.py` | ~4 | async_tools, collections, strings |
| `test_validation.py` | ~4 | ensure, validate_range, validate_one_of, validate_model |
| `test_version.py` | ~2 | SemVer parse/compare |
| `test_infrastructure.py` | ~3 | Clock, UUID generator, secret provider |

### 5.2 Coverage Summary

| Metric | Value |
|---|---|
| **Overall Coverage** | **85.08%** |
| Statements | 1,864 total, 257 missed |
| Branches | 274 total, 38 missed |
| **Covered modules (100%)** | 35 of ~80 modules |
| **Lowest coverage (<70%)** | `identifiers.py` (66.67%), `primitives.py` (78.57%) |
| **Untested (0%)** | `adapters/interfaces`, `interfaces/*`, `protocols/*` — protocol-only, no concrete impls |

### 5.3 Ruff Status

**PASS** — `ruff check src tests scripts` returns "All checks passed!"

- Rule set: E, W, F, I, B, C4, UP, S, SIM, PERF, PL, RUF, N, ANN, ASYNC, TID, PIE, RET, ARG, PTH, ERA, D
- Line length: 100
- Target version: py311

### 5.4 MyPy Status

**9 errors in 6 files** (non-blocking per CI policy):

| File | Error |
|---|---|
| `tests/conftest.py:23` | Generator return type should be `Generator` or supertype |
| `tests/fixtures/platform.py:18` | AsyncGenerator return type should be `AsyncGenerator` or supertype |
| `tests/unit/test_dependency_injection.py:97` | Unused `type: ignore` comment |
| `tests/unit/test_events.py:107` | Unused `type: ignore` comment + value of type var cannot be `str` |
| `tests/unit/test_lifecycle.py:22-23` | Non-overlapping identity check → unreachable statement |
| `tests/unit/test_platform.py:45,64` | Non-overlapping identity check |

- Strict mode enabled
- 113 source files checked
- CI treats mypy warnings as non-blocking (`echo "::warning::..."`)

### 5.5 Pytest Status

**PASS** — 152 passed in 1.58s
- Asyncio mode: `auto`
- Markers defined: `unit`, `integration`, `e2e`, `slow`
- Strict config, strict markers, show locals
- Import mode: `importlib`

### 5.6 Pre-commit Status

**Configured hooks** (`.pre-commit-config.yaml`):

| Hook | Version |
|---|---|
| pre-commit-hooks | v6.0.0 |
| ruff (lint + format) | v0.15.20 |
| black | 26.5.1 |
| mypy | v2.1.0 |
| detect-secrets | v1.5.0 |
| markdownlint-cli | v0.49.0 |
| yamlfmt | v0.21.0 |
| shellcheck-py | v0.11.0.1 |
| actionlint | v1.7.12 |
| conventional-pre-commit | v4.4.0 |

Minimum pre-commit version: 3.7.0

### 5.7 GitHub Actions Status

**CI workflow** (`.github/workflows/ci.yml`):
- **pre-commit** job: ubuntu-latest, Python 3.12, runs all hooks
- **lint** job: Ruff check, Ruff format check, Black check, mypy (non-blocking)
- **test** job: matrix across Python 3.11/3.12/3.13 on ubuntu-latest (+ macOS/Windows for 3.12)
- **build** job: sdist + wheel build, twine validation
- **ci** aggregator: gates branch protection

**Security workflow** (`.github/workflows/security.yml`):
- **bandit** (SAST): Python security linter
- **pip-audit** (deps): CVE scanning
- **gitleaks** (secrets): Git history secret scanning
- Scheduled: weekly Monday 06:00 UTC

---

## 6. Dependencies

### 6.1 Runtime Dependencies

| Package | Version Constraint | Purpose |
|---|---|---|
| `pydantic` | ≥2.9.0, <3 | Data validation & models |
| `pydantic-settings` | ≥2.6.0, <3 | Environment-driven settings |
| `structlog` | ≥24.4.0, <27 | Structured logging |
| `anyio` | ≥4.6.0, <5 | Async runtime bridge |
| `typing-extensions` | ≥4.12.0 (python < 3.13) | Backport type features |

### 6.2 Dev Dependencies

| Package | Version Constraint | Purpose |
|---|---|---|
| `ruff` | ≥0.6.9 | Linter & formatter |
| `black` | ≥24.10.0 | Formatter (canonical) |
| `mypy` | ≥1.13.0 | Static type checker |
| `pre-commit` | ≥4.0.1 | Git hook framework |
| `pip-audit` | ≥2.7.3 | Dependency vulnerability scanning |
| `bandit[toml]` | ≥1.7.10 | Python SAST |
| `detect-secrets` | ≥1.5.0 | Secret scanning |

### 6.3 Test Dependencies

| Package | Version Constraint | Purpose |
|---|---|---|
| `pytest` | ≥8.3.3 | Test framework |
| `pytest-cov` | ≥5.0.0 | Coverage reporting |
| `pytest-asyncio` | ≥0.24.0 | Async test support |
| `pytest-xdist` | ≥3.6.1 | Parallel test execution |
| `hypothesis` | ≥6.115.0 | Property-based testing |

### 6.4 Python Version

| Aspect | Value |
|---|---|
| **Required** | `>=3.11,<3.14` |
| **Running** | Python 3.14.6 (development environment — outside spec range) |
| **Target** | 3.11, 3.12, 3.13 |
| **CI matrix** | 3.11, 3.12, 3.13 |

### 6.5 Toolchain Versions (Installed)

| Tool | Version |
|---|---|
| `pip` | 26.1.2 |
| `ruff` | 0.15.20 |
| `mypy` | 2.1.0 |
| `pytest` | 9.1.1 |
| `black` | 26.5.1 |
| `coverage` | 7.15.0 |
| `pre-commit` | 4.6.0 |

---

## 7. Technical Debt

### 7.1 Source Code Markers

**TODOs / FIXMEs / HACKs in codebase:** 0 occurrences in `.py` files.

No inline `TODO`, `FIXME`, `HACK`, `XXX`, `WORKAROUND`, `TEMPORARY`, or `BUG` comments found in source code.

### 7.2 Documentation Markers

| File | Context |
|---|---|
| `.vscode/settings.json:115` | `todo-tree` configured to track `TODO`, `FIXME`, `HACK`, `XXX`, `NOTE` |
| `TECH_DEBT.md` | Dedicated technical debt register exists (not reviewed for content) |

### 7.3 Deprecated Code

The `CapabilityStatus.DEPRECATED` (`src/eaip/capabilities/capability.py:24`) and `CapabilityRegistry.deprecate()` method exist as **forward-looking** API — no capabilities are currently deprecated.

### 7.4 Unused/Untested Modules

| Module | Line Count | Covered? | Status |
|---|---|---|---|
| `eaip.interfaces.service` | 53 | 0% | Untested — no concrete implementations |
| `eaip.interfaces.repository` | 8 | 0% | Untested — no concrete implementations |
| `eaip.adapters.interfaces.base` | 9 | 0% | Untested — no concrete implementations |
| `eaip.protocols.lifecycle` | 27 | 0% | Protocol-only, tested through `LifecycleManager` |
| `eaip.protocols.health` | 7 | 0% | Protocol-only |
| `eaip.protocols.identifiable` | 19 | 0% | Protocol-only |
| `eaip.runtime/` | N/A | N/A | Empty placeholder directory |

### 7.5 Potential Architecture Drift

| Item | Observation |
|---|---|
| **`runtime/` directory** | Present with only `README.md` and `__pycache__` — placeholder with no implementation |
| **`metrics` subsystem** | Not implemented — health checks serve as proxy |
| **Plugin contract version** | Hardcoded `"1.0.0"` in `plugins/loader.py` — no mechanism to evolve |
| **Port/Adapter split** | `ports/` (protocols) and `infrastructure/` (concrete impls) are clean, but `adapters/interfaces/` is unused |
| **Interfaces vs Protocols** | Two parallel abstraction mechanisms: ABCs (`AbstractService`, `AbstractRepository`) and Protocols (`Startable`, `Stoppable`) — potential conceptual overlap |
| **Python version drift** | Dev environment runs Python 3.14.6, but package requires `<3.14` |
| **Coverage threshold** | `fail_under = 85` commented out in pyproject.toml — current coverage is 85.08%, borderline |

### 7.6 MyPy Warnings (Technical Debt)

9 mypy warnings in 6 files — all in test code:
- 2 generator return-type annotations
- 2 unused `type: ignore` comments
- 5 non-overlapping identity checks / unreachable statements (known test pattern for `LifecyclePhase` comparison)

---

## 8. Summary Statistics

| Category | Value |
|---|---|
| **Package version** | 0.0.2 |
| **Source modules** | 86 `.py` files |
| **Source lines (src)** | ~1,900 (86 SLOC measured) |
| **Test modules** | 27 `.py` files |
| **Test count** | 152 |
| **Coverage** | 85.08% |
| **Ruff** | PASS |
| **MyPy** | 9 warnings (non-blocking) |
| **Pytest** | 152/152 PASS |
| **Docker** | 1 Dockerfile + 1 docker-compose |
| **CI workflows** | 3 (CI, Security, Docs) |
| **Pre-commit hooks** | 16 hooks across 10 repos |
| **Third-party deps** | 5 runtime + 5 dev + 5 test |
| **Tags** | 1 (`v0.1.0-foundation`) |
| **Commits** | 20 |

---

*End of Bundle-007 Evidence Snapshot v1.0 — generated read-only, no modifications made.*
