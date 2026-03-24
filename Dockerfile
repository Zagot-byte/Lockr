# Multi-stage Dockerfile for Lockr Secrets Manager
# Optimized for production use with security best practices

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY setup.py README.md ./
COPY cli ./cli
COPY server ./server
COPY intent ./intent

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Runtime stage
FROM python:3.11-slim

LABEL maintainer="Lockr Team <hello@lockr.dev>"
LABEL description="Git-style secrets manager with post-quantum encryption and SOC-2 compliance"
LABEL version="0.1.0"

# Create non-root user for security
RUN groupadd -r lockr && \
    useradd -r -g lockr -u 1000 -m -s /bin/bash lockr

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=lockr:lockr cli ./cli
COPY --chown=lockr:lockr server ./server
COPY --chown=lockr:lockr intent ./intent
COPY --chown=lockr:lockr setup.py README.md ./

# Create vault directory
RUN mkdir -p /app/.vault && chown -R lockr:lockr /app/.vault

# Switch to non-root user
USER lockr

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VAULT_ROOT=/app/.vault

# Default command: start API server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
