# EAIP Security Review

> **Date:** 2026-07-11
> **Status:** Review complete — no critical findings

---

## Scope

Full repository review: `src/eaip/` (1,710 files, 148,963 lines).

## Security Controls

| Control | Status | Location |
|---------|--------|----------|
| JWT Authentication | ✅ Implemented | `auth/tokens.py` |
| JWT Secret Management | ✅ EnvSecretProvider | `auth/tokens.py:99-110` |
| Password Handling | ✅ No plaintext storage | `auth/auth_providers.py` |
| Input Validation | ✅ Pydantic everywhere | All models use frozen + extra=forbid |
| AST Sandbox | ✅ Restricted exec | `shared/sandbox.py` |
| Subprocess Safety | ✅ create_subprocess_exec | `automation/executor.py:113` |
| SQL Injection Protection | ⚠️ Parameterized + table name validation needed | `infrastructure/postgres_repository.py` |
| Secrets Scanning | ✅ detect-secrets baseline | `.secrets.baseline` |
| Dependency Scanning | ✅ pip-audit in CI | `.github/workflows/security.yml` |
| SAST Scanning | ✅ bandit in CI | `.github/workflows/security.yml` |
| CORS | ❌ Not implemented | Future work |
| CSRF | ❌ Not implemented | Future work |
| Rate Limiting | ⚠️ Token bucket exists | `gateway/ratelimit.py` |
| Tenant Isolation | ✅ TenantContext + TenantAwareRepository | `shared/tenant.py` |

## Findings

### Finding SR-01 (from WP-01A): AST Sandbox Attribute Escalation
- **Status:** Mitigated
- **Location:** `src/eaip/shared/sandbox.py`
- **Risk:** Low — 13 dangerous dunder attributes blocked
- **Residual risk:** Attribute-based class traversal via `__subclasses__` still theoretically possible but blocked

### Finding SEC-01: SQL Injection Risk (PostgresRepository)
- **Status:** Accepted — Low risk
- **Location:** `src/eaip/infrastructure/postgres_repository.py`
- **Risk:** Low — `table_name` parameter could allow injection if user-controlled
- **Mitigation:** Validate `table_name` against an allowlist before Beta RC

### Finding SEC-02: CORS/CSRF Not Implemented
- **Status:** Accepted — Future work
- **Risk:** Low — API is not exposed directly in current deployment topology
- **Mitigation:** Add CORS middleware and CSRF tokens before public API launch

## Vulnerability Scanning

| Tool | Result |
|------|--------|
| bandit | ✅ No medium+ findings |
| pip-audit | ✅ No vulnerabilities found |
| detect-secrets | ✅ No secrets detected |
| gitleaks | ✅ No secrets detected (CI) |

## Security Architecture

```
Client Request
     │
     ▼
[API Gateway / Rate Limiter]
     │
     ▼
[Authentication → JWT Validation → TokenService]
     │
     ▼
[Authorization → RBAC/ABAC → PolicyEngine]
     │
     ▼
[Service Layer → Pydantic validation → Port → Adapter]
     │
     ▼
[Audit Trail → EventBus → DomainEvent → Observability]
```

## Secrets Management

| Secret | Resolution | Source |
|--------|-----------|--------|
| JWT Signing Key | `EnvSecretProvider` | `EAIP_AUTH_SECRET` env var |
| Database Password | `EnvSecretProvider` | `EAIP_DB_PASSWORD` env var |
| API Keys | `FileSecretProvider` | `/etc/eaip/secrets.json` |

## Secure by Default

- All Pydantic models: `frozen=True, extra="forbid"`
- All tokens: configurable TTL with rotation
- No hardcoded credentials in source
- No `print()` or debug statements
- No `exec()` without AST validation
- No `subprocess_shell` — only `subprocess_exec`
