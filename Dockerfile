# ==============================================================================
# Multi-Agent AI System - Production Container Image
# Multi-service support: FastAPI REST API (port 8000) & Streamlit UI (port 8501)
# ==============================================================================

FROM python:3.12-slim AS base

# Set environment variables for optimized Python execution
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     PIP_DISABLE_PIP_VERSION_CHECK=1     PORT=8000

# Install minimal OS dependencies required for networking & healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends     curl     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create a non-privileged user for security compliance
RUN groupadd -g 10001 appgroup &&     useradd -u 10000 -g appgroup -s /bin/bash -m appuser

# Copy dependency requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Create application data directories for SQLite and ChromaDB persistence
RUN mkdir -p /app/data/chroma &&     chown -R appuser:appgroup /app

# Copy application source code and configuration
COPY src/ /app/src/
COPY .env.example /app/.env.example

# Grant non-root user permissions over the app workspace
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose FastAPI backend and Streamlit frontend ports
EXPOSE 8000 8501

# Default health check targeting FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Default command launches FastAPI backend via Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
