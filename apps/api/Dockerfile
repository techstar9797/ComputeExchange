# ComputeExchange API Server Docker Image

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared types first
COPY packages/shared-types /app/packages/shared-types

# Copy OpenEnv environment (needed for environment imports)
COPY openenv /app/openenv

# Copy agents
COPY agents /app/agents

# Copy API server
COPY apps/api /app/apps/api

# Copy data
COPY data /app/data

# Install Python dependencies
RUN pip install --no-cache-dir pydantic fastapi uvicorn websockets httpx

# Set environment variables
ENV PYTHONPATH=/app:/app/packages/shared-types:/app/openenv/compute_market_env:/app/agents
ENV PORT=8000

WORKDIR /app/apps/api

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
