# ComputeExchange Deployment Guide

## Overview

ComputeExchange consists of three services:

1. **Frontend** (Next.js) - Port 3000
2. **API** (FastAPI) - Port 8000
3. **OpenEnv Environment** (FastAPI) - Port 8001

## Prerequisites

- Node.js >= 18
- Python >= 3.10
- Docker (for containerized deployment)

## Local Development

```bash
make install
make dev
```

Or individually:
```bash
make dev-web   # http://localhost:3000
make dev-api   # http://localhost:8000
make dev-env   # http://localhost:8001
```

## Docker Deployment

### Build OpenEnv Environment

```bash
make docker-build
# or
docker build -t compute-market-env:latest ./openenv/compute_market_env
```

### Run OpenEnv Environment

```bash
make docker-run
# or
docker run -p 8001:8001 compute-market-env:latest
```

### Full Stack with Docker Compose (Optional)

Create `docker-compose.yml` in the project root:

```yaml
services:
  env:
    build: ./openenv/compute_market_env
    ports:
      - "8001:8001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      - ENV_BASE_URL=http://env:8001
    depends_on:
      - env

  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on:
      - api
```

*Note: Dockerfiles for API and web may need to be added. Currently only the OpenEnv env has a Dockerfile.*

## Hugging Face Spaces

The OpenEnv environment can be deployed to Hugging Face Spaces:

```bash
# Install openenv CLI
pip install openenv

# Push environment
openenv push --repo-id your-org/compute-market-env
```

Update `ENV_BASE_URL` in the API to point to your Spaces URL.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV_BASE_URL` | OpenEnv environment server URL | `http://localhost:8001` |
| `NEXT_PUBLIC_API_URL` | API server URL for frontend | `http://localhost:8000` |

## Health Checks

- **OpenEnv**: `GET http://localhost:8001/health`
- **API**: `GET http://localhost:8000/health` (if implemented)
- **Frontend**: Load `http://localhost:3000`

## Verify Docker Build

```bash
make docker-build
make docker-run
# In another terminal: curl http://localhost:8001/health
```

## Trajectory Export Validation

Validate RL training export format:

```bash
# Schema-only (no server required)
make validate-trajectory

# Against running API
python scripts/validate_trajectory_export.py --base-url http://localhost:8000
```
