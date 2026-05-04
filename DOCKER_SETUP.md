# Docker Setup Guide - Personal Podcast Generator

Complete guide for deploying the Personal Podcast Generator using Docker. This guide covers both development and production deployments with comprehensive troubleshooting.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Development Mode](#development-mode)
5. [Environment Configuration](#environment-configuration)
6. [Architecture Overview](#architecture-overview)
7. [Managing Services](#managing-services)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Installation

**macOS:**
```bash
brew install --cask docker
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

**Windows:**
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Verify Installation

```bash
docker --version
docker-compose --version
```

### Required API Keys

You'll need API keys from these services:

1. **OpenAI** (GPT-4o): https://platform.openai.com/api-keys
2. **ElevenLabs** (TTS): https://elevenlabs.io/app/settings/api-keys
3. **Firecrawl** (Web scraping): https://firecrawl.dev/app/api-keys

## Quick Start

Get the application running in under 5 minutes:

```bash
# 1. Clone the repository
git clone <repository-url>
cd personal-podcast-generator

# 2. Create environment file
cp .env.docker.example .env

# 3. Edit .env and add your API keys
nano .env  # or use your preferred editor

# 4. Deploy with one command
./scripts/docker-deploy.sh
```

That's it! The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Production Deployment

### Step 1: Environment Configuration

```bash
# Copy the example environment file
cp .env.docker.example .env

# Edit the file with your actual configuration
nano .env
```

**Minimum required configuration:**

```env
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...

# Database (use strong passwords in production!)
POSTGRES_PASSWORD=your_secure_password_here

# Application
ENVIRONMENT=production
DEBUG=False
```

### Step 2: Deploy Services

```bash
# Using the deployment script (recommended)
./scripts/docker-deploy.sh

# Or manually
docker-compose build
docker-compose up -d
```

### Step 3: Verify Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/health
```

### Step 4: Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

## Development Mode

Development mode provides:
- **Hot-reload** for both frontend and backend
- **Source code mounting** for live updates
- **Debug logging** enabled
- **Direct database access**

### Starting Development Environment

```bash
# Using the development script (recommended)
./scripts/docker-dev.sh

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Development Features

#### Backend Hot-Reload
Any changes to Python files will automatically restart the server:
```bash
# Edit a file
nano backend/app/api/podcasts.py

# Server automatically reloads - no restart needed!
```

#### Frontend Hot-Reload
React changes are reflected instantly:
```bash
# Edit a component
nano frontend/src/components/PodcastCard.tsx

# Browser automatically refreshes
```

#### Direct Database Access
```bash
# Connect to PostgreSQL directly
docker-compose exec db psql -U podcast_user -d podcast_db

# Run SQL commands
SELECT * FROM podcasts LIMIT 5;
```

#### Debug Backend
```bash
# View backend logs
docker-compose logs -f backend

# Execute commands in backend container
docker-compose exec backend bash
python -m app.db_init
```

### Stopping Development Environment

```bash
# Stop services (keep data)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove all data
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## Environment Configuration

### Complete Environment Reference

```env
# ==============================================================================
# Database Configuration
# ==============================================================================
POSTGRES_USER=podcast_user              # Database username
POSTGRES_PASSWORD=podcast_password      # Database password (change in production!)
POSTGRES_DB=podcast_db                  # Database name
POSTGRES_PORT=5432                      # Database port

# ==============================================================================
# Application Configuration
# ==============================================================================
ENVIRONMENT=production                  # production | development
DEBUG=False                            # Enable debug mode
SQL_ECHO=False                         # Log SQL queries

# ==============================================================================
# Service Ports
# ==============================================================================
BACKEND_PORT=8000                      # Backend API port
FRONTEND_PORT=3000                     # Frontend web port

# ==============================================================================
# API Keys
# ==============================================================================
OPENAI_API_KEY=sk-...                  # OpenAI API key
ELEVENLABS_API_KEY=...                 # ElevenLabs API key
FIRECRAWL_API_KEY=...                  # Firecrawl API key

# ==============================================================================
# Optional: Advanced Settings
# ==============================================================================
UVICORN_WORKERS=4                      # Number of worker processes
LOG_LEVEL=info                         # debug | info | warning | error
MAX_UPLOAD_SIZE=10                     # Max file upload size (MB)
AUDIO_TIMEOUT=300                      # Audio generation timeout (seconds)
```

### Environment Files

The project uses multiple environment files:

```
.env                    # Active configuration (not in git)
.env.docker.example     # Template for Docker deployment
backend/.env.example    # Template for backend-only development
```

## Architecture Overview

### Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                   (podcast_network)                      │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Frontend   │      │   Backend    │                │
│  │   (Nginx)    │─────▶│  (FastAPI)   │                │
│  │   Port: 80   │      │  Port: 8000  │                │
│  └──────────────┘      └──────┬───────┘                │
│         │                     │                         │
│         │                     │                         │
│         │              ┌──────▼───────┐                 │
│         │              │  PostgreSQL  │                 │
│         │              │  Port: 5432  │                 │
│         │              └──────────────┘                 │
│         │                                               │
│  ┌──────▼─────────────────────────────────────┐        │
│  │           Named Volumes                     │        │
│  │  - postgres_data (DB persistence)           │        │
│  │  - audio_files (Generated podcasts)         │        │
│  │  - backend_logs (Application logs)          │        │
│  └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Container Details

#### Frontend Container
- **Base Image**: node:20-alpine (build), nginx:alpine (runtime)
- **Build**: Multi-stage build for optimized production image
- **Size**: ~50MB (production)
- **Features**:
  - SPA routing with nginx
  - Gzip compression
  - API proxy to backend
  - Static asset caching

#### Backend Container
- **Base Image**: python:3.11-slim
- **Build**: Multi-stage build with separate builder stage
- **Size**: ~300MB
- **Features**:
  - FFmpeg for audio processing
  - PostgreSQL client tools
  - Auto-migration on startup
  - Health checks
  - Uvicorn with multiple workers

#### Database Container
- **Base Image**: postgres:15-alpine
- **Size**: ~230MB
- **Features**:
  - Automatic initialization
  - Health checks
  - Data persistence via volumes
  - UUID and full-text search extensions

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect personal-podcast-generator_audio_files

# Backup audio files
docker run --rm -v personal-podcast-generator_audio_files:/data \
  -v $(pwd):/backup alpine tar czf /backup/audio-backup.tar.gz /data

# Restore audio files
docker run --rm -v personal-podcast-generator_audio_files:/data \
  -v $(pwd):/backup alpine tar xzf /backup/audio-backup.tar.gz -C /
```

## Managing Services

### Starting Services

```bash
# Start all services (detached)
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Start with logs
docker-compose up

# Rebuild and start
docker-compose up --build
```

### Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop backend

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since 30m frontend
```

### Executing Commands

```bash
# Backend shell
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend alembic upgrade head

# PostgreSQL shell
docker-compose exec db psql -U podcast_user -d podcast_db

# Frontend shell
docker-compose exec frontend sh
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend

# Restart with rebuild
docker-compose up -d --build backend
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: "Bind for 0.0.0.0:8000 failed: port is already allocated"

**Solution**:
```bash
# Find process using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
BACKEND_PORT=8001
```

#### 2. Database Connection Failed

**Error**: "FATAL: password authentication failed"

**Solution**:
```bash
# Remove old volumes
docker-compose down -v

# Verify .env file
cat .env | grep POSTGRES

# Restart services
docker-compose up -d
```

#### 3. Backend Not Starting

**Error**: "Backend container exits immediately"

**Solution**:
```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Missing API keys in .env
# - Database not ready
# - Python dependency issues

# Rebuild backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

#### 4. Frontend Shows API Errors

**Error**: "Network Error" or "CORS error"

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Verify nginx proxy config
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

#### 5. Audio Generation Fails

**Error**: "FFmpeg not found"

**Solution**:
```bash
# Verify FFmpeg is installed in container
docker-compose exec backend which ffmpeg

# Rebuild backend if missing
docker-compose build --no-cache backend
```

#### 6. Database Migration Errors

**Error**: "Alembic migration failed"

**Solution**:
```bash
# Check current migration
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Reset database (WARNING: destroys data!)
docker-compose down -v
docker-compose up -d
```

### Health Checks

```bash
# Check service health status
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/health

# Check database connectivity
docker-compose exec backend python -c "from app.core.database import engine; print('OK')"
```

### Performance Issues

#### High CPU Usage

```bash
# Check container stats
docker stats

# If backend is high:
# - Reduce UVICORN_WORKERS in .env
# - Check for infinite loops in logs
# - Verify audio processing tasks
```

#### High Memory Usage

```bash
# Check memory usage
docker stats --no-stream

# Solutions:
# - Limit container memory in docker-compose.yml
# - Clear audio cache
# - Restart services
```

### Debugging Techniques

#### Enable Debug Logging

```bash
# Edit .env
DEBUG=True
LOG_LEVEL=debug

# Restart services
docker-compose restart backend
```

#### Interactive Debugging

```bash
# Start backend with bash
docker-compose run --rm backend bash

# Run Python commands
python -m app.db_init
python -c "import app; print(app.__version__)"
```

#### Database Debugging

```bash
# Connect to database
docker-compose exec db psql -U podcast_user -d podcast_db

# Check tables
\dt

# Check connections
SELECT * FROM pg_stat_activity;

# Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public';
```

## Advanced Configuration

### Custom Domain Setup

```bash
# Add to docker-compose.yml under frontend environment:
environment:
  - VIRTUAL_HOST=podcast.yourdomain.com
  - LETSENCRYPT_HOST=podcast.yourdomain.com
  - LETSENCRYPT_EMAIL=admin@yourdomain.com
```

### Scaling Services

```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3

# Note: You'll need a load balancer (nginx-proxy) for this
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Monitoring and Logging

```bash
# Enable JSON logging
environment:
  LOG_FORMAT=json

# Ship logs to external service
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Backup and Restore

#### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T db pg_dump -U podcast_user podcast_db > backup_db_$DATE.sql

# Backup audio files
docker run --rm -v personal-podcast-generator_audio_files:/data \
  -v $(pwd):/backup alpine tar czf /backup/backup_audio_$DATE.tar.gz /data

echo "Backup complete: $DATE"
```

#### Restore from Backup

```bash
# Restore database
cat backup_db_20240504.sql | docker-compose exec -T db psql -U podcast_user -d podcast_db

# Restore audio files
docker run --rm -v personal-podcast-generator_audio_files:/data \
  -v $(pwd):/backup alpine tar xzf /backup/backup_audio_20240504.tar.gz -C /
```

### Security Best Practices

1. **Change default passwords** in production
2. **Use secrets management** for API keys (Docker Secrets or external vault)
3. **Enable HTTPS** with reverse proxy (nginx-proxy + Let's Encrypt)
4. **Regular updates**: `docker-compose pull && docker-compose up -d`
5. **Monitor logs** for suspicious activity
6. **Backup regularly** using automated scripts

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to server
        run: |
          ssh user@server 'cd /app && git pull && ./scripts/docker-deploy.sh'
```

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Docker Documentation**: https://docs.docker.com
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **React Documentation**: https://react.dev

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Check GitHub issues
4. Contact the development team

---

**Built with professional DevOps practices for Prosper AI**
