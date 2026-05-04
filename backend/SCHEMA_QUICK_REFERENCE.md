# Database Schema Quick Reference

## Files Created

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py          # Exports database components
│   │   └── database.py          # Async SQLAlchemy engine and session management
│   ├── models/
│   │   ├── __init__.py          # Exports all models
│   │   ├── user.py              # User model with preferences and scheduling
│   │   ├── podcast.py           # Podcast model with status tracking
│   │   └── metrics.py           # Performance metrics and cost tracking
│   └── db_init.py               # Database initialization script
├── alembic/
│   ├── env.py                   # Alembic async environment configuration
│   └── versions/                # Migration files (created via alembic)
├── alembic.ini                  # Alembic configuration
├── verify_schema.py             # Schema verification script
└── DATABASE.md                  # Comprehensive documentation

```

## Quick Start

### 1. Set Environment Variable

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/podcast_generator"
```

### 2. Initialize Database (Development)

```bash
cd backend
python -m app.db_init
```

### 3. Or Use Alembic (Production)

```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Models Overview

### User
- **Purpose**: Store user preferences and scheduling settings
- **Key Fields**: `preferences` (JSONB), `schedule_settings` (JSONB)
- **Methods**: `get_default_preferences()`, `get_default_schedule_settings()`, `to_dict()`

### Podcast
- **Purpose**: Track podcast generation lifecycle
- **Key Fields**: `script`, `audio_url`, `status` (enum)
- **Status Values**: `pending`, `processing`, `completed`, `failed`
- **Methods**: `mark_processing()`, `mark_completed()`, `mark_failed()`, `to_dict()`

### Metrics
- **Purpose**: Track performance and costs
- **Key Fields**: `tokens_used`, `elevenlabs_characters`, `latency_ms`, `cost_estimate`
- **Methods**: `calculate_cost()`, `update_cost_estimate()`, `get_performance_summary()`

## Common Queries

### Create User
```python
from app.models import User
user = User(
    preferences=User.get_default_preferences(),
    schedule_settings=User.get_default_schedule_settings()
)
session.add(user)
await session.commit()
```

### Create Podcast
```python
from app.models import Podcast, PodcastStatus
podcast = Podcast(user_id=user_id, status=PodcastStatus.PENDING)
session.add(podcast)
await session.commit()
```

### Update Podcast Status
```python
podcast.mark_processing()
# ... generate podcast ...
podcast.mark_completed(audio_url="s3://bucket/podcast.mp3")
await session.commit()
```

### Record Metrics
```python
from app.models import Metrics
metrics = Metrics(
    podcast_id=podcast_id,
    tokens_used=2500,
    elevenlabs_characters=1200,
    latency_ms=15000
)
metrics.update_cost_estimate()
session.add(metrics)
await session.commit()
```

### Query with Relationships
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(User).where(User.id == user_id).options(selectinload(User.podcasts))
)
user = result.scalar_one()
podcasts = user.podcasts
```

## Indexes

### Single Column Indexes
- `users.id`, `users.created_at`, `users.updated_at`
- `podcasts.id`, `podcasts.user_id`, `podcasts.status`, `podcasts.created_at`
- `metrics.id`, `metrics.podcast_id`, `metrics.created_at`, `metrics.cost_estimate`

### Composite Indexes
- `(user_id, status)` - Filter podcasts by user and status
- `(user_id, created_at)` - Get user's recent podcasts
- `(status, created_at)` - Process podcast queue

## Connection Configuration

```python
pool_size=20              # Max connections
max_overflow=10           # Additional when full
pool_recycle=3600         # Recycle after 1 hour
pool_pre_ping=True        # Health check before use
```

## Verification

```bash
# Verify schema
python verify_schema.py

# Check Alembic status
alembic current

# Test database connection
python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect())"
```

## Cost Calculation

```python
# Default pricing (GPT-4o + ElevenLabs)
gpt_cost = (tokens_used / 1000) * 0.03
elevenlabs_cost = (characters / 1000) * 0.30
total_cost = gpt_cost + elevenlabs_cost
```

## Relationships

```
User (1) ──► (N) Podcast (1) ──► (1) Metrics
```

- User can have many Podcasts
- Podcast belongs to one User
- Podcast has one Metrics record
- Cascade delete from User to Podcasts to Metrics

## Key Features

✓ **Async SQLAlchemy 2.0** - Modern async/await patterns
✓ **UUID Primary Keys** - Better for distributed systems
✓ **JSONB Fields** - Flexible schema for preferences
✓ **Enum Status** - Type-safe podcast states
✓ **Comprehensive Indexes** - Optimized query performance
✓ **Relationship Loading** - Efficient eager loading with selectinload
✓ **Cost Tracking** - Built-in cost calculation methods
✓ **Performance Metrics** - Detailed timing breakdowns
✓ **Check Constraints** - Data integrity validation
✓ **Alembic Migrations** - Production-ready schema management
