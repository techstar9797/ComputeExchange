# OpenEnv Space: ComputeMarketEnv
# Connect: ComputeMarketEnv(base_url="https://mavericks97-ComputeExchange1.hf.space")

FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/techstar9797/ComputeExchange.git repo
WORKDIR /app/repo

RUN pip install --no-cache-dir -e ./packages/shared-types
RUN pip install --no-cache-dir -e ./openenv/compute_market_env

ENV PORT=8000
EXPOSE 8000

WORKDIR /app/repo/openenv/compute_market_env
ENV PYTHONPATH=/app/repo:/app/repo/packages/shared-types:/app/repo/openenv/compute_market_env

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
