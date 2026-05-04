# Multi-stage build for production-ready Python backend
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Add local Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/audio_files /app/logs

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Make startup script executable
RUN chmod +x /app/scripts/docker-startup.sh

# Use startup script as entrypoint
ENTRYPOINT ["/app/scripts/docker-startup.sh"]
