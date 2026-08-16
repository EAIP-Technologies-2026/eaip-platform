# =============================================================================
# EAIP — Backend Platform Image
# -----------------------------------------------------------------------------
# Multi-stage build for local development and production distribution.
# =============================================================================

FROM python:3.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── Builder Stage ────────────────────────────────────────────────────────────
FROM base AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        make \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/eaip/__init__.py src/eaip/__init__.py
COPY src/eaip/_version.py src/eaip/_version.py
COPY src/eaip/py.typed src/eaip/py.typed
COPY src/ ./src/

RUN python -m pip install --upgrade pip wheel setuptools hatchling \
 && python -m pip wheel --no-deps --wheel-dir /build/wheels . \
 && python -m pip wheel --wheel-dir /build/wheels ".[production]"

# ── Development Stage ────────────────────────────────────────────────────────
FROM builder AS development
ENV EAIP_CORE__ENVIRONMENT=development
WORKDIR /workspaces/eaip-platform
COPY . .
RUN python -m pip install -e ".[dev,test]"
CMD ["python", "-m", "eaip"]

# ── Production Stage ─────────────────────────────────────────────────────────
FROM base AS production

ENV EAIP_CORE__ENVIRONMENT=production

RUN addgroup --system --gid 1001 eaip && \
    adduser --system --uid 1001 --gid 1001 eaip

WORKDIR /app

COPY --from=builder /build/wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* \
 && rm -rf /wheels

USER eaip
EXPOSE 8080

CMD ["python", "-m", "eaip"]
