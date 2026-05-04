# Database Schema Documentation

## Overview

This document describes the PostgreSQL database schema for the Personal Podcast Generator application. The schema uses async SQLAlchemy with proper indexes, relationships, and constraints for production-grade performance.

## Architecture

- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (async)
- **Driver**: asyncpg
- **Migrations**: Alembic

## Models

### 1. User Model (`users` table)

Stores user information, preferences, and scheduling settings.

**Columns:**
- `id` (UUID, PK): Unique user identifier
- `preferences` (JSONB): User interests, topics, sources, and content preferences
- `schedule_settings` (JSONB): Automated podcast generation schedule configuration
- `created_at` (DateTime, indexed): User creation timestamp
- `updated_at` (DateTime, indexed): Last update timestamp

**Relationships:**
- One-to-Many with Podcast (cascade delete)

**Example preferences structure:**
```json
{
  "interests": ["technology", "AI", "startups"],
  "topics": ["machine learning", "web development"],
  "sources": ["TechCrunch", "Hacker News"],
  "language": "en",
  "duration_minutes": 10,
  "voice_settings": {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}
```

**Example schedule_settings structure:**
```json
{
  "enabled": true,
  "frequency": "daily",
  "time": "08:00",
  "timezone": "UTC",
  "days_of_week": [1, 2, 3, 4, 5]
}
```

### 2. Podcast Model (`podcasts` table)

Stores generated podcast episodes and their status.

**Columns:**
- `id` (UUID, PK): Unique podcast identifier
- `user_id` (UUID, FK, indexed): Foreign key to users table
- `script` (Text): Generated podcast script content
- `audio_url` (String): URL or path to generated audio file
- `status` (Enum): Current status (pending, processing, completed, failed)
- `error_message` (Text): Error details if generation failed
- `metadata` (Text): Additional metadata in JSON format
- `created_at` (DateTime, indexed): Podcast creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- Many-to-One with User
- One-to-One with Metrics

**Indexes:**
- Composite index on (user_id, status)
- Composite index on (user_id, created_at)
- Composite index on (status, created_at)

**Status Enum Values:**
- `pending`: Podcast generation job has been queued
- `processing`: Podcast is currently being generated
- `completed`: Podcast generation completed successfully
- `failed`: Podcast generation failed

### 3. Metrics Model (`metrics` table)

Tracks performance metrics and costs for podcast generation.

**Columns:**
- `id` (UUID, PK): Unique metrics identifier
- `podcast_id` (UUID, FK, unique, indexed): Foreign key to podcasts table (one-to-one)
- `tokens_used` (Integer): Number of tokens consumed by GPT-4o
- `elevenlabs_characters` (Integer): Number of characters processed by ElevenLabs TTS
- `latency_ms` (Integer): Total end-to-end latency in milliseconds
- `cost_estimate` (Float, indexed): Estimated cost in USD
- `news_fetch_ms` (Integer): Time taken to fetch news articles
- `script_generation_ms` (Integer): Time taken to generate script
- `audio_generation_ms` (Integer): Time taken to generate audio
- `created_at` (DateTime, indexed): Metrics recording timestamp

**Relationships:**
- One-to-One with Podcast

**Constraints:**
- CHECK constraint: tokens_used >= 0
- CHECK constraint: elevenlabs_characters >= 0
- CHECK constraint: latency_ms >= 0
- CHECK constraint: cost_estimate >= 0

**Cost Calculation:**
```python
# Default pricing (adjust as needed)
GPT_4O_COST_PER_1K_TOKENS = 0.03  # $0.03 per 1K tokens
ELEVENLABS_COST_PER_1K_CHARS = 0.30  # $0.30 per 1K characters

cost = (tokens / 1000 * 0.03) + (characters / 1000 * 0.30)
```

## Database Setup

### Environment Variables

Set the following environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/podcast_generator
```

### Initialize Database (Development)

For development/testing, you can create tables directly:

```bash
cd backend
python -m app.db_init
```

### Alembic Migrations (Production)

For production, use Alembic migrations:

```bash
cd backend

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Rollback one version
alembic downgrade -1
```

## Usage Examples

### Creating a Session

```python
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

async def example_endpoint(session: AsyncSession = Depends(get_session)):
    # Use session here
    pass
```

### Creating a User

```python
from app.models import User

async def create_user(session: AsyncSession):
    user = User(
        preferences=User.get_default_preferences(),
        schedule_settings=User.get_default_schedule_settings()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### Creating a Podcast

```python
from app.models import Podcast, PodcastStatus

async def create_podcast(user_id: UUID, session: AsyncSession):
    podcast = Podcast(
        user_id=user_id,
        status=PodcastStatus.PENDING
    )
    session.add(podcast)
    await session.commit()
    await session.refresh(podcast)
    return podcast
```

### Recording Metrics

```python
from app.models import Metrics

async def record_metrics(podcast_id: UUID, session: AsyncSession):
    metrics = Metrics(
        podcast_id=podcast_id,
        tokens_used=2500,
        elevenlabs_characters=1200,
        latency_ms=15000,
        news_fetch_ms=3000,
        script_generation_ms=8000,
        audio_generation_ms=4000
    )
    metrics.update_cost_estimate()
    session.add(metrics)
    await session.commit()
    return metrics
```

### Querying with Relationships

```python
from sqlalchemy import select
from app.models import User, Podcast

async def get_user_podcasts(user_id: UUID, session: AsyncSession):
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.podcasts))
    )
    user = result.scalar_one()
    return user.podcasts
```

## Performance Considerations

### Indexes

The schema includes several indexes to optimize common queries:

1. **Single column indexes:**
   - `users.id`, `users.created_at`, `users.updated_at`
   - `podcasts.id`, `podcasts.user_id`, `podcasts.status`, `podcasts.created_at`
   - `metrics.id`, `metrics.podcast_id`, `metrics.created_at`, `metrics.cost_estimate`

2. **Composite indexes:**
   - `(user_id, status)` - For filtering podcasts by user and status
   - `(user_id, created_at)` - For getting user's recent podcasts
   - `(status, created_at)` - For processing queue management

### Connection Pooling

The database configuration includes connection pooling:

```python
pool_size=20          # Maximum number of connections
max_overflow=10       # Additional connections when pool is full
pool_recycle=3600     # Recycle connections after 1 hour
pool_pre_ping=True    # Check connection health before use
```

### JSONB Performance

The `preferences` and `schedule_settings` columns use PostgreSQL's JSONB type for:
- Efficient storage and indexing
- Fast queries on JSON fields
- Flexible schema evolution

To query JSONB fields:

```python
from sqlalchemy.dialects.postgresql import JSONB

# Query by JSONB field
result = await session.execute(
    select(User).where(
        User.preferences['language'].astext == 'en'
    )
)
```

## Backup and Maintenance

### Database Backup

```bash
# Backup database
pg_dump -U postgres podcast_generator > backup.sql

# Restore database
psql -U postgres podcast_generator < backup.sql
```

### Vacuum and Analyze

For optimal performance, regularly vacuum and analyze:

```sql
VACUUM ANALYZE users;
VACUUM ANALYZE podcasts;
VACUUM ANALYZE metrics;
```

## Schema Diagram

```
┌─────────────────────┐
│       Users         │
├─────────────────────┤
│ id (PK)            │
│ preferences        │
│ schedule_settings  │
│ created_at         │
│ updated_at         │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐      ┌─────────────────────┐
│      Podcasts       │ 1:1  │      Metrics        │
├─────────────────────┤◄─────┤─────────────────────┤
│ id (PK)            │      │ id (PK)            │
│ user_id (FK)       │      │ podcast_id (FK)    │
│ script             │      │ tokens_used        │
│ audio_url          │      │ elevenlabs_chars   │
│ status             │      │ latency_ms         │
│ error_message      │      │ cost_estimate      │
│ metadata           │      │ news_fetch_ms      │
│ created_at         │      │ script_gen_ms      │
│ updated_at         │      │ audio_gen_ms       │
└─────────────────────┘      │ created_at         │
                             └─────────────────────┘
```

## Testing

For testing, use a separate database:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/podcast_generator_test
```

Consider using fixtures for test data:

```python
import pytest
from app.models import User, Podcast, Metrics

@pytest.fixture
async def test_user(session):
    user = User(
        preferences=User.get_default_preferences(),
        schedule_settings=User.get_default_schedule_settings()
    )
    session.add(user)
    await session.commit()
    return user
```

## Migration Strategy

When making schema changes:

1. **Development**: Test changes locally first
2. **Create migration**: `alembic revision --autogenerate -m "Description"`
3. **Review migration**: Check the generated migration file
4. **Test migration**: Apply to test database
5. **Production**: Apply with monitoring

```bash
# Safe production migration
alembic upgrade head

# If issues occur, rollback
alembic downgrade -1
```
