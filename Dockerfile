# Dockerfile for macOS Cleaner Web Interface
# Copyright (c) 2026 macOS Cleaner contributors

FROM python:3.11-slim

# Set metadata
LABEL maintainer="macOS Cleaner contributors <contributors@mac-cleaner.local>"
LABEL description="Safe and comprehensive macOS system cleaner - Web Interface"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r maccleaner && useradd -r -g maccleaner maccleaner

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml setup.py ./

# Install the application
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R maccleaner:maccleaner /app

# Copy configuration files
COPY config/ ./config/
COPY templates/ ./templates/
COPY static/ ./static/

# Switch to non-root user
USER maccleaner

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["mac-cleaner-web", "--host", "0.0.0.0", "--port", "5000"]
