# =============================================================================
# EAIP — Local development image
# -----------------------------------------------------------------------------
# Used by `docker compose -f docker-compose.dev.yml up` and by CI for
# reproducible "works on my machine" parity. Production images for individual
# capabilities ship from their own engineering packages.
# =============================================================================

FROM python:3.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    EAIP_CORE__ENVIRONMENT=development

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        make \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/eaip-platform

# Copy only files needed for dependency resolution first to maximise layer cache hits.
COPY pyproject.toml ./
COPY src/eaip/__init__.py src/eaip/__init__.py
COPY src/eaip/_version.py src/eaip/_version.py
COPY src/eaip/py.typed src/eaip/py.typed

RUN python -m pip install --upgrade pip wheel setuptools \
 && python -m pip install -e ".[dev,test]"

# Copy the rest after deps so editing source doesn't bust the dep layer.
COPY . .

CMD ["bash"]
