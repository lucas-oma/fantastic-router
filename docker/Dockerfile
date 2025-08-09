FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        curl \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY packages/fantastic_router_core/pyproject.toml packages/fantastic_router_core/pyproject.toml
COPY packages/fantastic_router_core/src packages/fantastic_router_core/src
COPY packages/fantastic_router_server/pyproject.toml packages/fantastic_router_server/pyproject.toml
COPY packages/fantastic_router_server/src packages/fantastic_router_server/src
COPY adapters adapters
COPY examples examples

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install -e "packages/fantastic_router_core[openai,postgres,dev]" \
    && pip install -e "packages/fantastic_router_server[dev]" \
    && pip install asyncpg openai python-dotenv

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Set Python path to include our modules
ENV PYTHONPATH=/app

# Default command
# CMD ["python", "examples/quickstart/example.py"] 
# Default command runs the FastAPI server
CMD ["python", "-m", "uvicorn", "fantastic_router_server.main:app", "--host", "0.0.0.0", "--port", "8000"] 