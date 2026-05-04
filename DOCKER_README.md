# Docker Deployment - Quick Reference

Complete Docker configuration for the Personal Podcast Generator with production-ready features.

## Quick Start

```bash
# 1. Setup environment
cp .env.docker.example .env
nano .env  # Add your API keys

# 2. Deploy
make deploy

# Access the app
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

## What's Included

### Docker Files
- **backend/Dockerfile** - Multi-stage Python 3.11 container with FFmpeg
- **frontend/Dockerfile** - Multi-stage Node 20 + Nginx container
- **docker-compose.yml** - Production orchestration
- **docker-compose.dev.yml** - Development mode with hot-reload
- **Makefile** - Convenient management commands

### Configuration Files
- **backend/.dockerignore** - Optimize backend build
- **frontend/.dockerignore** - Optimize frontend build
- **frontend/nginx.conf** - Production Nginx with SPA routing, gzip, API proxy
- **docker/init-db.sql** - PostgreSQL initialization

### Scripts
- **backend/scripts/docker-startup.sh** - Backend startup with migrations
- **scripts/docker-deploy.sh** - Production deployment script
- **scripts/docker-dev.sh** - Development mode script

### Documentation
- **DOCKER_SETUP.md** - Comprehensive setup and troubleshooting guide

## Architecture

```
Frontend (Nginx) → Backend (FastAPI) → PostgreSQL
      ↓                  ↓                  ↓
   Port 80           Port 8000         Port 5432
      ↓                  ↓                  ↓
  React SPA         Python 3.11      Postgres 15
   + Nginx          + FFmpeg         + Extensions
```

### Named Volumes
- **postgres_data** - Database persistence
- **audio_files** - Generated podcast audio files
- **backend_logs** - Application logs

## Key Features

### Production Ready
✅ Multi-stage builds for minimal image sizes
✅ Health checks for all services
✅ Automatic database migrations on startup
✅ Proper signal handling and graceful shutdown
✅ Security headers and gzip compression
✅ Volume persistence for data

### Development Friendly
✅ Hot-reload for backend and frontend
✅ Source code mounting for live updates
✅ Debug logging enabled
✅ Direct database access
✅ Separate dev configuration

### DevOps Best Practices
✅ Docker Compose orchestration
✅ Environment-based configuration
✅ Health monitoring endpoints
✅ Centralized logging
✅ Easy backup and restore
✅ Resource management

## Common Commands

```bash
# Using Makefile (recommended)
make deploy          # Deploy production
make dev             # Start development mode
make logs            # View all logs
make status          # Check service health
make migrate         # Run database migrations
make backup          # Backup database and files
make clean           # Remove all containers and volumes

# Using Docker Compose directly
docker-compose up -d                    # Start services
docker-compose down                     # Stop services
docker-compose logs -f backend          # View backend logs
docker-compose exec backend bash        # Backend shell
docker-compose exec db psql -U podcast_user -d podcast_db  # DB shell
```

## Service Details

### Backend Container
- **Base**: Python 3.11-slim
- **Size**: ~300MB
- **Includes**: FFmpeg, PostgreSQL client
- **Workers**: 4 (production), 1 with reload (dev)
- **Startup**: Waits for DB → Runs migrations → Starts uvicorn

### Frontend Container
- **Base**: Node 20-alpine (build) + Nginx-alpine (runtime)
- **Size**: ~50MB
- **Features**: SPA routing, API proxy, gzip, caching
- **Build time**: ~2-3 minutes

### Database Container
- **Base**: PostgreSQL 15-alpine
- **Size**: ~230MB
- **Extensions**: uuid-ossp, pg_trgm
- **Initialization**: Automatic on first start

## Environment Variables

Required in `.env`:

```env
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...

# Database (optional, has defaults)
POSTGRES_PASSWORD=podcast_password
POSTGRES_USER=podcast_user
POSTGRES_DB=podcast_db

# Application
ENVIRONMENT=production
DEBUG=False
```

See `.env.docker.example` for complete reference.

## Port Mapping

| Service  | Container Port | Host Port | Configurable |
|----------|---------------|-----------|--------------|
| Frontend | 80            | 3000      | Yes (FRONTEND_PORT) |
| Backend  | 8000          | 8000      | Yes (BACKEND_PORT) |
| Database | 5432          | 5432      | Yes (POSTGRES_PORT) |

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Verify API keys in .env
cat .env | grep API_KEY

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database connection fails
```bash
# Wait for database to be ready
docker-compose logs db

# Check database health
docker-compose exec db pg_isready -U podcast_user
```

### Port already in use
```bash
# Change port in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001

# Restart services
docker-compose down
docker-compose up -d
```

See **DOCKER_SETUP.md** for comprehensive troubleshooting.

## Advanced Usage

### Development Mode
```bash
# Start with hot-reload
make dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Backup and Restore
```bash
# Backup
make backup

# Restore database
make restore-db file=backups/db_20240504.sql

# Restore audio files
docker run --rm -v personal-podcast-generator_audio_files:/data \
  -v $(pwd):/backup alpine tar xzf /backup/audio_20240504.tar.gz -C /
```

### Scaling Backend
```bash
# Run multiple backend instances
docker-compose up -d --scale backend=3

# Note: Requires load balancer setup
```

### Resource Limits
Edit `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

## Monitoring

```bash
# Service status
make status

# Container stats
docker stats

# Health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/health

# Database queries
docker-compose exec db psql -U podcast_user -d podcast_db \
  -c "SELECT COUNT(*) FROM podcasts;"
```

## Security Considerations

1. **Change default passwords** in production `.env`
2. **Restrict database port** - remove from `ports:` in production
3. **Use HTTPS** with reverse proxy (nginx-proxy + Let's Encrypt)
4. **Regular updates**: `docker-compose pull && docker-compose up -d`
5. **Enable firewall** on host machine
6. **Monitor logs** for suspicious activity

## Performance Tips

1. **Use SSD storage** for Docker volumes
2. **Adjust worker count** in `.env` (UVICORN_WORKERS)
3. **Enable database connection pooling** (already configured)
4. **Use CDN** for static assets in production
5. **Monitor resource usage**: `docker stats`

## CI/CD Integration

The Docker setup is CI/CD ready:

```yaml
# Example GitHub Actions
- name: Deploy
  run: |
    docker-compose build
    docker-compose up -d
    docker-compose exec backend alembic upgrade head
```

## File Structure

```
├── docker-compose.yml           # Production orchestration
├── docker-compose.dev.yml       # Development overrides
├── .env.docker.example          # Environment template
├── Makefile                     # Management commands
├── DOCKER_SETUP.md             # Full documentation
├── DOCKER_README.md            # This file
├── backend/
│   ├── Dockerfile              # Backend container
│   ├── .dockerignore           # Build optimization
│   └── scripts/
│       └── docker-startup.sh   # Startup script
├── frontend/
│   ├── Dockerfile              # Frontend container
│   ├── .dockerignore           # Build optimization
│   └── nginx.conf              # Nginx configuration
├── docker/
│   └── init-db.sql             # DB initialization
└── scripts/
    ├── docker-deploy.sh        # Production deploy
    └── docker-dev.sh           # Development mode
```

## Next Steps

1. **Read DOCKER_SETUP.md** for comprehensive documentation
2. **Configure .env** with your API keys
3. **Run `make deploy`** to start the application
4. **Access the dashboard** at http://localhost:3000
5. **Check API docs** at http://localhost:8000/docs

## Support

- **Documentation**: See DOCKER_SETUP.md
- **Troubleshooting**: Check logs with `make logs`
- **Health checks**: Run `make status`

---

**Built with professional DevOps practices for Prosper AI**

Demonstrates: Multi-stage builds, health checks, volume management, proper orchestration, security best practices, and production-ready configuration.
