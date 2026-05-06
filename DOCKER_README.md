# Docker Quick Reference Guide

Quick reference for running the Personal Podcast Generator with Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB free disk space
- API Keys: OpenAI, ElevenLabs, Firecrawl, News API

## Quick Start

```bash
# 1. Copy environment file
cp .env.docker.example .env

# 2. Edit .env and add your API keys
nano .env  # or use your preferred editor

# 3. Start all services
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Check status
docker-compose ps
```

## Service Access

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React web interface |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| PostgreSQL | localhost:5432 | Database (internal) |

## Common Commands

### Start Services
```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d backend
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild After Code Changes
```bash
# Rebuild all images
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

## Database Management

### Access PostgreSQL
```bash
# Via docker exec
docker exec -it podcast_db psql -U podcast_user -d podcast_db

# List databases
docker exec podcast_db psql -U podcast_user -c "\l"

# List tables
docker exec podcast_db psql -U podcast_user -d podcast_db -c "\dt"
```

### Run Migrations
```bash
# Migrations run automatically on startup
# To run manually:
docker exec podcast_backend alembic upgrade head

# Create new migration
docker exec podcast_backend alembic revision --autogenerate -m "description"
```

### Backup Database
```bash
# Create backup
docker exec podcast_db pg_dump -U podcast_user podcast_db > backup.sql

# Restore backup
docker exec -i podcast_db psql -U podcast_user podcast_db < backup.sql
```

## Development vs Production

### Development Mode
Uses `docker-compose.dev.yml` with:
- Live code reloading
- Debug mode enabled
- Source code mounted as volumes
- Exposed database port

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production Mode
Uses `docker-compose.prod.yml` with:
- Optimized builds
- Resource limits
- Security hardening
- No exposed database port

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Variables

Required variables in `.env`:

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...
NEWS_API_KEY=...

# Database (use defaults for Docker)
POSTGRES_USER=podcast_user
POSTGRES_PASSWORD=podcast_password
POSTGRES_DB=podcast_db

# JWT Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this-in-production
```

See `.env.docker.example` for all available options.

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs db
```

**Common issues:**
- Missing API keys in `.env`
- Port already in use (3000, 8000, 5432)
- Insufficient disk space

### Database Connection Errors

```bash
# Check if database is healthy
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Frontend Can't Connect to Backend

**Check backend health:**
```bash
curl http://localhost:8000/health
```

**Verify CORS settings:**
- Backend CORS should allow `http://localhost:3000`
- Check `backend/app/main.py` CORS configuration

### Port Already in Use

**Find process using port:**
```bash
# macOS/Linux
lsof -i :3000  # or :8000, :5432

# Kill process
kill -9 <PID>
```

**Or change port in `.env`:**
```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

### Out of Disk Space

**Clean up Docker:**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything (⚠️ careful!)
docker system prune -a --volumes
```

### Migrations Failed

```bash
# Check migration status
docker exec podcast_backend alembic current

# View migration history
docker exec podcast_backend alembic history

# Reset to specific migration
docker exec podcast_backend alembic downgrade <revision>
docker exec podcast_backend alembic upgrade head
```

## Data Persistence

Data is stored in Docker volumes:
- `postgres_data` - Database data
- `audio_files` - Generated podcast MP3 files
- `backend_logs` - Application logs

**Location:**
```bash
# View volumes
docker volume ls | grep podcast

# Inspect volume
docker volume inspect podcast_postgres_data

# Backup volume
docker run --rm -v podcast_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v podcast_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/health  # Frontend
docker exec podcast_db pg_isready  # Database
```

## Performance Optimization

### Resource Limits (Production)
Edit `docker-compose.prod.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        memory: 512M
```

### Scale Services
```bash
# Run multiple backend workers
docker-compose up -d --scale backend=3
```

## Security Best Practices

1. **Change default credentials** in `.env`
2. **Use strong SECRET_KEY**: `openssl rand -hex 32`
3. **Don't expose database port** in production
4. **Keep API keys secure** - never commit `.env` to git
5. **Use HTTPS** with reverse proxy (nginx/caddy) in production
6. **Regular updates**: `docker-compose pull && docker-compose up -d`

## Monitoring

### View Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats podcast_backend
```

### Log Rotation
Production logs are stored in `backend_logs` volume. Consider log rotation:

```bash
# View log size
docker exec podcast_backend du -sh /app/logs

# Clear old logs
docker exec podcast_backend find /app/logs -name "*.log" -mtime +7 -delete
```

## Next Steps

- **See full setup guide:** [SETUP.md](SETUP.md)
- **See detailed Docker guide:** [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **API documentation:** http://localhost:8000/docs
- **Report issues:** [GitHub Issues](https://github.com/yourusername/personal-podcast-generator/issues)

## Quick Reference

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Access database
docker exec -it podcast_db psql -U podcast_user -d podcast_db

# Check health
docker-compose ps

# Clean up
docker-compose down -v  # ⚠️ Deletes all data
```
