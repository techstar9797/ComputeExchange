# ComputeMarketEnv Docker Image
# For deployment to Hugging Face Spaces or other container platforms

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml .
COPY server/requirements.txt ./server/

# Install Python dependencies
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir pydantic fastapi uvicorn websockets

# Copy the rest of the code
COPY . .

# Copy shared types
COPY ../../packages/shared-types /app/packages/shared-types

# Set environment variables
ENV PYTHONPATH=/app:/app/packages/shared-types
ENV PORT=8001
ENV ENABLE_WEB_INTERFACE=true

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8001"]
