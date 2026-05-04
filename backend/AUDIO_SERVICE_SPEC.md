# Audio Generation Service - Technical Specification

## Service Overview

The `ElevenLabsAudioService` is a production-grade async service that converts podcast scripts into high-quality audio using ElevenLabs Text-to-Speech API.

## API Reference

### ElevenLabsAudioService

#### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    storage_path: Optional[str] = None,
) -> None
```

**Parameters:**
- `api_key`: ElevenLabs API key (default: from `settings.ELEVENLABS_API_KEY`)
- `storage_path`: Local storage directory (default: `/tmp/podcasts`)

**Example:**
```python
service = ElevenLabsAudioService(
    api_key="sk-...",
    storage_path="/var/podcasts"
)
```

#### Main Methods

##### generate_audio()

```python
async def generate_audio(
    self,
    script: PodcastScript,
    podcast_id: str,
    voice_settings: Optional[Dict[str, VoiceSettings]] = None,
) -> AudioGenerationResponse
```

**Parameters:**
- `script`: PodcastScript with segments from ScriptGeneratorService
- `podcast_id`: Unique identifier (UUID string)
- `voice_settings`: Optional custom voice configuration per speaker

**Returns:** `AudioGenerationResponse` containing:
- `success`: bool - Whether generation succeeded
- `audio_file`: AudioFile - File metadata and metrics
- `error_message`: Optional[str] - Error details if failed

**Raises:**
- `ElevenLabsAPIError`: API-related errors after retries
- `IOError`: File system errors
- `ValueError`: Invalid input parameters

**Example:**
```python
response = await service.generate_audio(
    script=script,
    podcast_id="123e4567-e89b-12d3-a456-426614174000",
)

if response.success:
    file_path = response.audio_file.file_path
    cost = response.audio_file.metrics.cost_estimate
```

#### Context Manager Support

```python
async with ElevenLabsAudioService() as service:
    response = await service.generate_audio(script, podcast_id)
    # Automatic cleanup on exit
```

#### Internal Methods

##### _get_voice_id()
Maps speaker to ElevenLabs voice ID.

```python
def _get_voice_id(self, speaker: SpeakerType) -> str
```

##### _generate_segment()
Generates audio for a single text segment with retry logic.

```python
async def _generate_segment(
    self,
    text: str,
    voice_id: str,
    voice_settings: Optional[VoiceSettings] = None,
    retry_count: int = 0,
) -> Tuple[bytes, int]
```

**Returns:** `(audio_bytes, latency_ms)`

##### _combine_segments()
Combines multiple audio segments into single file.

```python
def _combine_segments(
    self,
    segments: List[AudioSegment]
) -> AudioSegment
```

##### _save_audio()
Saves audio to local storage.

```python
def _save_audio(
    self,
    audio_data: AudioSegment,
    podcast_id: str
) -> Tuple[str, int]
```

**Returns:** `(file_path, file_size_bytes)`

### Factory Function

```python
async def get_audio_service() -> ElevenLabsAudioService
```

FastAPI dependency injection factory. Use with `Depends()`:

```python
@app.post("/audio/generate")
async def generate(
    service: ElevenLabsAudioService = Depends(get_audio_service)
):
    response = await service.generate_audio(script, podcast_id)
    return response
```

## Data Models

### AudioFile

```python
class AudioFile(BaseModel):
    podcast_id: str
    file_path: str
    file_url: Optional[str]
    file_size_bytes: int
    duration_seconds: float
    format: str = "mp3"
    sample_rate: int = 44100
    channels: int = 1
    bitrate_kbps: int = 128
    metrics: AudioMetrics
    created_at: datetime
```

### AudioMetrics

```python
class AudioMetrics(BaseModel):
    total_characters: int
    total_latency_ms: int
    segment_count: int
    segment_metrics: List[AudioSegmentMetrics]
    cost_estimate: float
    api_calls: int
    retries: int = 0
    model_used: str = "multilingual_v2"
```

### AudioSegmentMetrics

```python
class AudioSegmentMetrics(BaseModel):
    segment_index: int
    speaker: Optional[str]
    character_count: int
    latency_ms: int
    voice_id: Optional[str]
    success: bool = True
    error_message: Optional[str] = None
```

### VoiceSettings

```python
class VoiceSettings(BaseModel):
    stability: float = 0.5           # 0.0 - 1.0
    similarity_boost: float = 0.75   # 0.0 - 1.0
    style: float = 0.0               # 0.0 - 1.0
    use_speaker_boost: bool = True
```

### AudioGenerationResponse

```python
class AudioGenerationResponse(BaseModel):
    success: bool
    audio_file: Optional[AudioFile] = None
    error_message: Optional[str] = None
```

## Configuration

### Constants

```python
# API Configuration
BASE_URL = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"

# Voice Mapping
VOICE_MAP = {
    SpeakerType.ALEX: "pNInz6obpgDQGcFmaJgB",   # Adam
    SpeakerType.SONIA: "EXAVITQu4vr4xnSDxMaL",  # Bella
}

# Pricing
COST_PER_1K_CHARS = 0.30  # USD

# Audio Settings
SAMPLE_RATE = 44100       # Hz
CHANNELS = 1              # Mono
BITRATE = 128             # kbps
FORMAT = "mp3"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0         # seconds
RETRY_BACKOFF = 2.0       # multiplier

# Rate Limiting
MAX_CONCURRENT_REQUESTS = 3
REQUEST_TIMEOUT = 60.0    # seconds

# Break Configuration
BREAK_DURATION_MS = 1000  # 1 second
```

### Environment Variables

```bash
ELEVENLABS_API_KEY=sk-...  # Required
```

## Integration Examples

### With Script Service

```python
from app.services import ScriptGeneratorService, ElevenLabsAudioService

# Generate script
script_service = ScriptGeneratorService()
script, script_metrics = await script_service.generate_script(
    news_articles=articles,
    preferences={"tone": "casual", "length": "medium"}
)

# Generate audio
async with ElevenLabsAudioService() as audio_service:
    response = await audio_service.generate_audio(
        script=script,
        podcast_id=str(uuid4())
    )
```

### With Database

```python
from app.models import Podcast, Metrics
from app.core.database import get_session

async def process_podcast(podcast_id: str, db: AsyncSession):
    # Get podcast
    podcast = await db.get(Podcast, podcast_id)

    # Generate audio
    async with ElevenLabsAudioService() as service:
        response = await service.generate_audio(
            script=podcast.script,
            podcast_id=str(podcast.id)
        )

    if response.success:
        # Update podcast
        podcast.mark_completed(response.audio_file.file_path)

        # Save metrics
        metrics = Metrics(
            podcast_id=podcast.id,
            elevenlabs_characters=response.audio_file.metrics.total_characters,
            audio_generation_ms=response.audio_file.metrics.total_latency_ms,
            cost_estimate=response.audio_file.metrics.cost_estimate,
        )
        db.add(metrics)
        await db.commit()
```

### With FastAPI Routes

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services import get_audio_service, ElevenLabsAudioService

router = APIRouter(prefix="/api/v1/audio", tags=["audio"])

@router.post("/generate/{podcast_id}")
async def generate_audio(
    podcast_id: str,
    service: ElevenLabsAudioService = Depends(get_audio_service),
    db: AsyncSession = Depends(get_session),
):
    # Get podcast
    podcast = await db.get(Podcast, podcast_id)
    if not podcast:
        raise HTTPException(404, "Podcast not found")

    # Parse script
    script = parse_podcast_script(podcast.script)

    # Generate audio
    response = await service.generate_audio(script, podcast_id)

    if not response.success:
        raise HTTPException(500, response.error_message)

    return {
        "file_path": response.audio_file.file_path,
        "duration": response.audio_file.duration_seconds,
        "cost": response.audio_file.metrics.cost_estimate,
    }
```

### With Background Tasks

```python
from celery import Celery

celery_app = Celery('podcast_generator')

@celery_app.task
async def generate_podcast_audio(podcast_id: str) -> dict:
    async with ElevenLabsAudioService() as service:
        # Get script
        script = await get_podcast_script(podcast_id)

        # Generate audio
        response = await service.generate_audio(script, podcast_id)

        if response.success:
            # Upload to S3
            file_url = await upload_to_s3(
                response.audio_file.file_path,
                podcast_id
            )

            # Update database
            await update_podcast_audio(podcast_id, file_url)

            return {
                "status": "success",
                "file_url": file_url,
                "metrics": response.audio_file.metrics.dict()
            }
        else:
            return {
                "status": "error",
                "error": response.error_message
            }
```

## Error Handling

### Exception Types

```python
class ElevenLabsAPIError(Exception):
    """Raised when ElevenLabs API request fails."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    )
```

### Error Scenarios

| Error | Cause | Handling |
|-------|-------|----------|
| `ElevenLabsAPIError` | API key invalid | Check `.env` configuration |
| `ElevenLabsAPIError(429)` | Rate limit exceeded | Automatic retry with backoff |
| `ElevenLabsAPIError(timeout)` | Request timeout | Automatic retry (3 attempts) |
| `ValueError` | Invalid speaker | Check voice mapping |
| `IOError` | File save failed | Check storage permissions |

### Retry Logic

```python
try:
    audio_bytes, latency = await service._generate_segment(
        text=text,
        voice_id=voice_id
    )
except ElevenLabsAPIError as e:
    if e.status_code == 429:
        # Rate limit - automatic retry
        await asyncio.sleep(RETRY_DELAY * (2 ** retry_count))
        # Retry...
    else:
        # Other API error - propagate
        raise
```

## Performance

### Latency Breakdown

For a typical 10-minute podcast (1,500 words):

| Stage | Time | % |
|-------|------|---|
| API Calls | 25-40s | 70% |
| Audio Processing | 5-10s | 20% |
| File I/O | 2-5s | 10% |
| **Total** | **30-60s** | **100%** |

### Optimization Strategies

1. **Parallel Processing**: Use `MAX_CONCURRENT_REQUESTS=3`
2. **Voice Caching**: Pre-warm voice IDs
3. **Segment Batching**: Combine short segments
4. **Async I/O**: Non-blocking file operations
5. **Connection Pooling**: Reuse HTTP connections

### Resource Usage

| Resource | Per Podcast | Notes |
|----------|-------------|-------|
| Memory | ~50-100 MB | Audio buffers |
| CPU | Low | Minimal processing |
| Network | ~10-15 MB | Download audio |
| Disk | ~10-15 MB | Final MP3 file |

## Cost Analysis

### Pricing Model

ElevenLabs charges per character processed:
- **$0.30 per 1,000 characters**

### Cost Examples

| Podcast Length | Words | Characters | Cost |
|---------------|-------|------------|------|
| Short (5 min) | 750 | ~5,000 | $1.50 |
| Medium (10 min) | 1,500 | ~10,000 | $3.00 |
| Long (15 min) | 2,250 | ~15,000 | $4.50 |

### Cost Optimization

1. **Script Optimization**: Remove filler words
2. **Voice Settings**: Adjust for efficiency
3. **Caching**: Store generated audio
4. **Batch Processing**: Combine similar requests

## Testing

### Unit Test Example

```python
import pytest
from app.services.audio_service import ElevenLabsAudioService

@pytest.mark.asyncio
async def test_generate_audio():
    service = ElevenLabsAudioService()
    script = create_test_script()

    response = await service.generate_audio(
        script=script,
        podcast_id="test-123"
    )

    assert response.success
    assert response.audio_file is not None
    assert response.audio_file.duration_seconds > 0
    assert response.audio_file.metrics.cost_estimate > 0
```

### Mock ElevenLabs API

```python
from unittest.mock import AsyncMock, patch

@patch('httpx.AsyncClient.post')
async def test_with_mock(mock_post):
    mock_post.return_value = AsyncMock(
        status_code=200,
        content=b'fake_audio_data'
    )

    service = ElevenLabsAudioService()
    response = await service.generate_audio(script, "test-123")

    assert response.success
    mock_post.assert_called_once()
```

## Monitoring

### Metrics to Track

```python
# Success rate
success_rate = successful_generations / total_generations

# Average latency
avg_latency = sum(latencies) / len(latencies)

# Cost per podcast
avg_cost = total_cost / podcast_count

# Error rate
error_rate = failed_generations / total_generations
```

### Logging

```python
import logging

logger = logging.getLogger('audio_service')

# Log levels:
# INFO: Generation start/complete, cost
# DEBUG: Segment processing details
# WARNING: Retries, rate limits
# ERROR: Failures with stack trace
```

## Security

### Best Practices

1. **API Key Management**
   - Store in environment variables
   - Never commit to version control
   - Rotate periodically

2. **Input Validation**
   - Validate all inputs with Pydantic
   - Sanitize file paths
   - Limit text length

3. **Error Messages**
   - Don't leak sensitive data
   - Log full details server-side
   - Return generic errors to client

4. **Rate Limiting**
   - Respect API limits
   - Implement backoff strategy
   - Monitor usage

## Deployment

### Production Checklist

- [ ] Set `ELEVENLABS_API_KEY` in environment
- [ ] Install ffmpeg on server
- [ ] Configure storage path with write permissions
- [ ] Set up log rotation
- [ ] Configure monitoring/alerting
- [ ] Test error scenarios
- [ ] Set up backup storage
- [ ] Document runbook procedures

### Docker Configuration

```dockerfile
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Create storage directory
RUN mkdir -p /tmp/podcasts

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**Issue:** "API key is invalid"
```bash
# Check environment variable
echo $ELEVENLABS_API_KEY

# Verify in .env file
cat .env | grep ELEVENLABS_API_KEY
```

**Issue:** "ffmpeg not found"
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Ubuntu
```

**Issue:** "Rate limit exceeded"
```python
# Reduce concurrent requests
MAX_CONCURRENT_REQUESTS = 2
```

**Issue:** "File save permission denied"
```bash
# Check permissions
ls -la /tmp/podcasts
chmod 755 /tmp/podcasts
```

## Support

For issues or questions:
- Documentation: `AUDIO_SERVICE_README.md`
- Examples: `example_audio_usage.py`
- ElevenLabs Docs: https://docs.elevenlabs.io/
