# EAIP Release Guide

## Versioning
EAIP follows Semantic Versioning: `MAJOR.MINOR.PATCH`

- **Pre-release**: `0.MINOR.PATCH-beta.N` (current)
- **Release Candidate**: `0.MINOR.PATCH-rc.N`
- **GA**: `1.MINOR.PATCH`

## Build Process

### Backend
```bash
cd eaip-platform
pip install -e .[dev,test]
python -m build  # creates dist/eaip-*.tar.gz and .whl
```

### Docker
```bash
docker compose build
docker compose up -d
```

### Frontend
```bash
cd eaip-frontend
pnpm install
pnpm build:packages
pnpm build
```

## Release Steps

1. Run full test suite
   ```bash
   cd eaip-platform && python -m pytest tests/ -v --asyncio-mode=auto
   cd eaip-frontend && pnpm test
   ```

2. Run type checking
   ```bash
   cd eaip-platform && mypy src/
   cd eaip-frontend && pnpm typecheck
   ```

3. Run linting
   ```bash
   cd eaip-platform && ruff check src/
   cd eaip-frontend && pnpm lint
   ```

4. Build Docker images
   ```bash
   cd eaip-platform && docker compose build
   ```

5. Tag release
   ```bash
   git tag v0.1.0-beta.1
   git push origin v0.1.0-beta.1
   ```

6. Generate release artifacts
   - Python wheel and source distribution
   - Docker images
   - Frontend static build
   - Environment template

## Deployment

### Production
```bash
docker compose -f docker-compose.yml up -d
```

### Environment Variables
See `.env` template for all required variables:
- `EAIP_AUTH_SECRET` — JWT signing secret (required)
- `EAIP_DB__*` — PostgreSQL connection (production)
- `EAIP_REDIS__*` — Redis connection (production)
