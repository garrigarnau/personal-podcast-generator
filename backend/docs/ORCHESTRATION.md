# Podcast Generation Orchestration

This document explains the async task orchestration layer for the Personal Podcast Generator. The orchestration system coordinates the complete podcast generation pipeline with comprehensive error handling, metrics tracking, and observability.

## Architecture Overview

The orchestration layer consists of two main components:

### 1. PodcastOrchestrator (`orchestrator.py`)

Coordinates the end-to-end podcast generation pipeline:
- News fetching (Firecrawl API)
- Script generation (OpenAI GPT-4o)
- Audio generation (ElevenLabs TTS)
- Storage and metrics collection

### 2. TaskManager (`task_manager.py`)

Manages background task execution with:
- Task queuing with priority support
- Concurrency limits
- Task status tracking
- Cancellation support
- Statistics and monitoring

## Pipeline Flow

```
User Request → Create Podcast Record → Queue Background Task
                                              ↓
                                    [TaskManager Queue]
                                              ↓
                                    PodcastOrchestrator
                                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │                                                           │
    ├→ 1. Update Status: PENDING → PROCESSING                  │
    │                                                           │
    ├→ 2. Fetch News Articles (Firecrawl)                     │
    │    - Filter by interests and recency                     │
    │    - Rank by relevance                                   │
    │    - Track latency and costs                             │
    │                                                           │
    ├→ 3. Generate Script (GPT-4o)                             │
    │    - Convert articles to conversational dialogue         │
    │    - Apply tone and length preferences                   │
    │    - Save script to database                             │
    │    - Track token usage and costs                         │
    │                                                           │
    ├→ 4. Generate Audio (ElevenLabs)                          │
    │    - Process script segments with multiple voices        │
    │    - Combine audio segments                              │
    │    - Save audio file locally                             │
    │    - Track character usage and costs                     │
    │                                                           │
    ├→ 5. Save Results                                         │
    │    - Update podcast with audio URL                       │
    │    - Save comprehensive metrics                          │
    │    - Update status: PROCESSING → COMPLETED               │
    │                                                           │
    └→ Error Handling: Mark as FAILED with error details       │
                                                               │
```

## Key Features

### Async-First Design

All operations are async to prevent blocking:
```python
async def generate_podcast_async(
    podcast_id: str,
    user_id: str,
    interests: List[str],
    preferences: Dict[str, Any],
) -> None:
    # All steps are async
    articles = await fetch_news(...)
    script = await generate_script(...)
    audio = await generate_audio(...)
```

### Database Status Tracking

Podcast status is updated at each stage:
- **PENDING**: Initial state, waiting to start
- **PROCESSING**: Currently being generated
- **COMPLETED**: Successfully generated with audio
- **FAILED**: Generation failed with error message

### Comprehensive Metrics

Tracks metrics at each stage:
```python
{
    "news_fetch_ms": 1234,
    "script_generation_ms": 5678,
    "audio_generation_ms": 45000,
    "tokens_used": 2500,
    "elevenlabs_characters": 3200,
    "cost_estimate": 0.15,
    "total_latency_ms": 52000
}
```

### Error Handling

Graceful error handling at each stage:
- Try/catch around each service call
- Save partial results on failure
- Mark podcast as failed with detailed error message
- Log all errors with full context

## Usage Examples

### Basic Usage (Direct Orchestrator)

```python
from app.services.orchestrator import PodcastOrchestrator
from app.core.database import get_session

async def generate_podcast(podcast_id: str, user_id: str):
    async with get_session() as db:
        orchestrator = PodcastOrchestrator(db)

        await orchestrator.generate_podcast_async(
            podcast_id=podcast_id,
            user_id=user_id,
            interests=["AI", "technology", "startups"],
            preferences={
                "tone": "casual",
                "length": "medium",
                "max_articles": 5,
                "days_back": 7
            }
        )
```

### FastAPI Integration (Background Task)

```python
from fastapi import BackgroundTasks
from app.services.orchestrator import trigger_podcast_generation

@router.post("/podcasts/generate")
async def generate_podcast(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    # Create podcast record
    podcast = Podcast(user_id=request.user_id, status=PodcastStatus.PENDING)
    db.add(podcast)
    await db.commit()

    # Trigger background generation
    background_tasks.add_task(
        trigger_podcast_generation,
        podcast_id=str(podcast.id),
        user_id=request.user_id,
        interests=request.interests,
        preferences={"tone": request.tone, "length": request.length},
        db=db
    )

    return {"podcast_id": str(podcast.id), "status": "pending"}
```

### TaskManager Integration (Advanced)

```python
from app.services.task_manager import get_task_manager, TaskPriority

@router.post("/podcasts/generate-with-priority")
async def generate_with_priority(request: GenerateRequest):
    task_manager = get_task_manager()

    # Submit task with high priority
    task_id = await task_manager.submit_podcast_generation(
        podcast_id=podcast_id,
        user_id=user_id,
        interests=["AI", "technology"],
        preferences={"tone": "casual", "length": "medium"},
        priority=TaskPriority.HIGH  # Jump to front of queue
    )

    return {"task_id": task_id, "podcast_id": podcast_id}
```

### Monitoring Task Status

```python
from app.services.task_manager import get_task_manager

# Get specific task status
task_manager = get_task_manager()
task_info = await task_manager.get_task_status(task_id)

if task_info:
    print(f"Status: {task_info.status.value}")
    print(f"Duration: {task_info.duration_seconds}s")
    if task_info.error_message:
        print(f"Error: {task_info.error_message}")

# Get all tasks for a user
user_tasks = await task_manager.get_user_tasks(user_id="user-123")
running_tasks = [t for t in user_tasks if t.status == TaskStatus.RUNNING]

# Get system statistics
stats = task_manager.get_statistics()
print(f"Active tasks: {stats['active_tasks']}")
print(f"Queue size: {stats['queue_size']}")
print(f"Completed: {stats['completed_tasks']}")
```

### Cancelling Tasks

```python
from app.services.task_manager import get_task_manager

task_manager = get_task_manager()
success = await task_manager.cancel_task(task_id)

if success:
    print("Task cancelled successfully")
else:
    print("Task could not be cancelled (may already be completed)")
```

## Configuration

### TaskManager Settings

Configure in initialization:
```python
task_manager = TaskManager(
    max_concurrent=5,      # Max parallel tasks
    enable_queue=True,     # Enable task queuing
    queue_max_size=100     # Max queue size (0 = unlimited)
)
```

### Orchestrator Settings

Configure via preferences dict:
```python
preferences = {
    # News fetching
    "max_articles": 5,              # Max articles to fetch
    "days_back": 7,                 # Only articles from last N days
    "min_relevance_score": 0.3,     # Minimum relevance threshold

    # Script generation
    "tone": "casual",               # serious, casual, balanced
    "length": "medium",             # short, medium, long

    # Audio generation
    "voice_settings": {             # Optional custom voice settings
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}
```

## API Endpoints

### Generate Podcast
```http
POST /api/v1/podcasts/generate
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "interests": ["AI", "technology", "startups"],
  "tone": "casual",
  "length": "medium",
  "sources": []
}

Response: 202 Accepted
{
  "id": "podcast-id",
  "status": "pending",
  "audio_url": null,
  "error_message": null,
  "progress": 0
}
```

### Poll Podcast Status
```http
GET /api/v1/podcasts/{podcast_id}/status

Response: 200 OK
{
  "id": "podcast-id",
  "status": "processing",  // pending, processing, completed, failed
  "audio_url": null,
  "error_message": null,
  "progress": 50
}
```

### Get Task Status
```http
GET /api/v1/tasks/{task_id}

Response: 200 OK
{
  "task_id": "task-id",
  "task_type": "podcast_generation",
  "status": "running",
  "priority": 2,
  "podcast_id": "podcast-id",
  "user_id": "user-id",
  "created_at": "2024-05-04T10:00:00",
  "started_at": "2024-05-04T10:00:01",
  "completed_at": null,
  "duration_seconds": null,
  "error_message": null,
  "metadata": {...}
}
```

### List User Tasks
```http
GET /api/v1/tasks/user/{user_id}?status_filter=running

Response: 200 OK
{
  "tasks": [...],
  "total": 5
}
```

### Cancel Task
```http
POST /api/v1/tasks/{task_id}/cancel

Response: 200 OK
{
  "success": true,
  "message": "Task cancelled successfully"
}
```

### Get Statistics
```http
GET /api/v1/tasks/

Response: 200 OK
{
  "total_tasks": 42,
  "active_tasks": 3,
  "queue_size": 5,
  "max_concurrent": 5,
  "queued_tasks": 5,
  "running_tasks": 3,
  "completed_tasks": 30,
  "failed_tasks": 3,
  "cancelled_tasks": 1
}
```

## Error Handling

### Pipeline Errors

Each stage has specific error handling:

**News Fetch Errors:**
- Network failures (retries with exponential backoff)
- Rate limiting (backoff and retry)
- No articles found (clear error message)

**Script Generation Errors:**
- OpenAI API failures (retries with exponential backoff)
- Token limits exceeded (clear error message)
- Invalid response format (parsing error handling)

**Audio Generation Errors:**
- ElevenLabs API failures (retries with exponential backoff)
- Character limits exceeded (clear error message)
- Audio processing failures (detailed error logging)

### Database Errors

Transaction management:
```python
try:
    # All database operations
    await db.flush()
    await db.commit()
except Exception as e:
    await db.rollback()
    raise
```

### Partial Results

On failure, partial results are saved:
- Script is saved even if audio generation fails
- Metrics are saved for completed stages
- Error message includes which stage failed

## Observability

### Logging

Comprehensive logging at each stage:
```python
logger.info(f"[{podcast_id}] Starting podcast generation")
logger.info(f"[{podcast_id}] Fetched {len(articles)} articles in {latency}ms")
logger.info(f"[{podcast_id}] Script generated: {word_count} words")
logger.info(f"[{podcast_id}] Audio generated: {duration}s")
logger.info(f"[{podcast_id}] Completed in {total_time}ms, cost ${cost}")
```

### Metrics Collection

Detailed metrics for every generation:
- Stage-by-stage timing
- Resource usage (tokens, characters)
- Cost estimates
- Success/failure rates

### Database Tracking

All statuses and metrics stored in database:
- Podcast status history
- Metrics per podcast
- Error messages and timestamps

## Production Considerations

### Concurrency Limits

Set appropriate limits based on:
- Available memory
- API rate limits
- Database connection pool size

Recommended: 3-5 concurrent tasks

### Queue Management

Monitor queue size:
```python
stats = task_manager.get_statistics()
if stats['queue_size'] > 50:
    logger.warning("High queue size, consider scaling")
```

### Resource Cleanup

Automatic cleanup on shutdown:
```python
# In application shutdown
task_manager = get_task_manager()
await task_manager.shutdown(timeout=60.0)
```

### Error Monitoring

Monitor failure rates:
```python
stats = task_manager.get_statistics()
failure_rate = stats['failed_tasks'] / stats['total_tasks']
if failure_rate > 0.1:  # 10% failure rate
    logger.error(f"High failure rate: {failure_rate:.2%}")
```

## Testing

### Unit Tests

Test individual components:
```python
import pytest
from app.services.orchestrator import PodcastOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_success(mock_db, mock_services):
    orchestrator = PodcastOrchestrator(mock_db)

    await orchestrator.generate_podcast_async(
        podcast_id="test-id",
        user_id="user-id",
        interests=["test"],
        preferences={}
    )

    # Verify status updated to completed
    assert podcast.status == PodcastStatus.COMPLETED
```

### Integration Tests

Test complete pipeline:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline(test_db, test_user):
    # Create podcast
    podcast = Podcast(user_id=test_user.id)
    test_db.add(podcast)
    await test_db.commit()

    # Run orchestrator
    orchestrator = PodcastOrchestrator(test_db)
    await orchestrator.generate_podcast_async(
        podcast_id=str(podcast.id),
        user_id=str(test_user.id),
        interests=["technology"],
        preferences={"tone": "casual", "length": "short"}
    )

    # Verify results
    await test_db.refresh(podcast)
    assert podcast.status == PodcastStatus.COMPLETED
    assert podcast.audio_url is not None
    assert podcast.script is not None
```

## Troubleshooting

### Common Issues

**Issue: Tasks stuck in PROCESSING**
- Check if background worker is running
- Verify no exceptions in logs
- Check database connection pool

**Issue: High failure rate**
- Check API keys and quotas
- Verify network connectivity
- Review error logs for patterns

**Issue: Slow generation**
- Check API response times
- Verify no rate limiting
- Consider increasing concurrency

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger("app.services.orchestrator").setLevel(logging.DEBUG)
logging.getLogger("app.services.task_manager").setLevel(logging.DEBUG)
```

## Performance Tips

1. **Adjust concurrency based on load:**
   ```python
   # Low traffic: 3 concurrent
   # High traffic: 5-10 concurrent
   ```

2. **Monitor queue depth:**
   - Alert if queue > 50 tasks
   - Scale workers if consistently high

3. **Optimize database queries:**
   - Use selectinload for relationships
   - Batch updates when possible

4. **Cache user preferences:**
   - Reduce database reads
   - Faster task execution

## Future Enhancements

- [ ] Priority lanes (separate queues per priority)
- [ ] Task retry logic with exponential backoff
- [ ] Persistent task queue (Redis/RabbitMQ)
- [ ] Distributed task execution (Celery)
- [ ] Real-time progress updates (WebSockets)
- [ ] Task scheduling (cron-like)
- [ ] Cost budgeting per user
- [ ] A/B testing for different pipelines
