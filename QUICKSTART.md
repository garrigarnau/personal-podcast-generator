# Quick Start Guide - Docker Deployment

Get the Personal Podcast Generator running in **under 5 minutes**.

## Prerequisites

- Docker and Docker Compose installed
- API keys for OpenAI, ElevenLabs, and Firecrawl

## 3-Step Deployment

### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.docker.example .env

# Edit and add your API keys
nano .env
```

Required keys:
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `ELEVENLABS_API_KEY` - Get from https://elevenlabs.io/app/settings/api-keys
- `FIRECRAWL_API_KEY` - Get from https://firecrawl.dev/app/api-keys

### Step 2: Deploy

```bash
make deploy
```

That's it! The script will:
- Validate your configuration
- Build Docker images
- Start all services
- Run database migrations
- Check health status

### Step 3: Access

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

## Common Commands

```bash
# View logs
make logs

# Check status
make status

# Stop services
make stop

# Restart services
make restart

# Development mode (with hot-reload)
make dev

# Run migrations
make migrate

# Backup data
make backup

# Remove everything
make clean
```

## Troubleshooting

### Port Already in Use

Edit `.env`:
```env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### API Keys Not Working

Check your `.env` file:
```bash
cat .env | grep API_KEY
```

Make sure there are no spaces around the `=` sign.

### Services Won't Start

```bash
# Check logs
make logs

# Restart from scratch
make clean
make deploy
```

### Database Connection Failed

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## Development Mode

For development with hot-reload:

```bash
make dev
```

Features:
- Backend auto-reloads on code changes
- Frontend auto-refreshes on code changes
- Debug logging enabled
- Direct database access

## Health Check

Verify everything is working:

```bash
./scripts/health-check.sh
```

This checks:
- All services are running
- Health endpoints respond
- Database is accessible
- Disk space is sufficient
- Logs show no errors

## What's Running?

After deployment, you have:

1. **PostgreSQL Database**
   - Port: 5432
   - Data persisted in Docker volume

2. **FastAPI Backend**
   - Port: 8000
   - 4 workers (production)
   - Auto-migrations on startup
   - Health checks enabled

3. **React Frontend**
   - Port: 3000 (actually 80 inside container)
   - Nginx serving static files
   - API proxy to backend
   - Gzip compression

## Next Steps

1. **Try it out**: Visit http://localhost:3000
2. **Read the docs**: See DOCKER_SETUP.md for comprehensive guide
3. **Explore the API**: Visit http://localhost:8000/docs

## Getting Help

- **Comprehensive Guide**: DOCKER_SETUP.md
- **Quick Reference**: DOCKER_README.md
- **File Overview**: DOCKER_FILES_SUMMARY.md
- **Completion Report**: DOCKER_DEPLOYMENT_COMPLETE.md

## Advanced Usage

### Production Deployment

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Custom Ports

Edit `.env`:
```env
BACKEND_PORT=8080
FRONTEND_PORT=80
```

### View Specific Logs

```bash
make logs-backend
make logs-frontend
make logs-db
```

### Database Shell

```bash
make shell-db
```

### Backend Shell

```bash
make shell-backend
```

## Success!

If you see this, you're ready:
```
Services running at:
  - Frontend: http://localhost:3000
  - Backend API: http://localhost:8000
  - API Docs: http://localhost:8000/docs
```

---

**Need more help?** See DOCKER_SETUP.md for detailed documentation with troubleshooting for 12 common issues.
