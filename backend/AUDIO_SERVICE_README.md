# ElevenLabs Audio Generation Service

Production-grade audio generation service for the Personal Podcast Generator using ElevenLabs Text-to-Speech API.

## Overview

The `ElevenLabsAudioService` converts podcast scripts into high-quality audio files with natural-sounding voices, smooth speaker transitions, and precise timing control.

### Key Features

- **Multi-Speaker Support**: Distinct voices for Alex and Sonia using ElevenLabs voice library
- **Natural Conversation Flow**: Smooth transitions between speakers with configurable pauses
- **Break Handling**: Automatic silence insertion for `[BREAK]` markers in scripts
- **Audio Combination**: Seamless merging of audio segments into final podcast file
- **Cost Tracking**: Real-time character count and cost estimation
- **Comprehensive Metrics**: Detailed latency, API call, and performance tracking
- **Error Handling**: Automatic retries with exponential backoff
- **Rate Limiting**: Built-in request throttling to respect API limits
- **Local Storage**: File-based storage with optional cloud upload support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  ElevenLabsAudioService                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Input: PodcastScript (from ScriptGeneratorService)          │
│         ├─ Segments (speaker + text)                         │
│         └─ Metadata (tone, length, topics)                   │
│                                                               │
│  Processing Pipeline:                                         │
│  ┌────────────────────────────────────────────────────┐      │
│  │ 1. Process each script segment                     │      │
│  │    ├─ Map speaker → ElevenLabs voice ID           │      │
│  │    ├─ Generate audio via API call                 │      │
│  │    ├─ Add silence for breaks                      │      │
│  │    └─ Track metrics per segment                   │      │
│  │                                                     │      │
│  │ 2. Combine audio segments                          │      │
│  │    ├─ Sequential concatenation                     │      │
│  │    ├─ Normalize audio format                       │      │
│  │    └─ Ensure consistent quality                    │      │
│  │                                                     │      │
│  │ 3. Save to storage                                 │      │
│  │    ├─ Export as MP3 (128kbps)                      │      │
│  │    ├─ Calculate file size                          │      │
│  │    └─ Return file path/URL                         │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  Output: AudioGenerationResponse                             │
│          ├─ AudioFile (path, URL, metadata)                  │
│          └─ AudioMetrics (cost, latency, API calls)          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `elevenlabs==1.10.0` - ElevenLabs API client
- `httpx==0.27.0` - Async HTTP client
- `pydub==0.25.1` - Audio processing
- `pydantic==2.9.2` - Data validation

### System Requirements

For audio processing, you also need ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Environment Setup

Add your ElevenLabs API key to `.env`:

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

Get your API key from: https://elevenlabs.io/

## Usage

### Basic Usage

```python
import asyncio
from app.services import ElevenLabsAudioService
from app.services.script_service import PodcastScript, ScriptSegment, SpeakerType

async def generate_audio():
    # Create or obtain a podcast script
    script = PodcastScript(
        segments=[
            ScriptSegment(
                speaker=SpeakerType.ALEX,
                text="Welcome to today's podcast!",
                order=0,
                pause_after=False,
            ),
            ScriptSegment(
                speaker=SpeakerType.SONIA,
                text="Thanks for joining us!",
                order=1,
                pause_after=True,  # Add 1-second silence after
            ),
        ],
        # ... other metadata
    )

    # Generate audio
    async with ElevenLabsAudioService() as audio_service:
        response = await audio_service.generate_audio(
            script=script,
            podcast_id="podcast-123",
        )

        if response.success:
            print(f"Audio saved to: {response.audio_file.file_path}")
            print(f"Duration: {response.audio_file.duration_seconds}s")
            print(f"Cost: ${response.audio_file.metrics.cost_estimate}")
        else:
            print(f"Error: {response.error_message}")

asyncio.run(generate_audio())
```

### Custom Voice Settings

```python
from app.schemas.audio import VoiceSettings

# Configure custom voice settings per speaker
voice_settings = {
    "ALEX": VoiceSettings(
        stability=0.6,
        similarity_boost=0.8,
        style=0.2,
        use_speaker_boost=True,
    ),
    "SONIA": VoiceSettings(
        stability=0.7,
        similarity_boost=0.85,
        style=0.1,
        use_speaker_boost=True,
    ),
}

response = await audio_service.generate_audio(
    script=script,
    podcast_id="podcast-123",
    voice_settings=voice_settings,
)
```

### Full Pipeline Example

```python
from app.services import ScriptGeneratorService, ElevenLabsAudioService
from app.services.script_service import NewsArticle

async def full_pipeline():
    # 1. Fetch news and generate script
    article = NewsArticle(
        title="AI Breakthrough",
        summary="New AI system achieves human-level performance",
        content="...",
        source="Tech News",
    )

    script_service = ScriptGeneratorService()
    script, script_metrics = await script_service.generate_script(
        news_articles=[article],
        preferences={"tone": "casual", "length": "medium"},
    )

    # 2. Generate audio from script
    async with ElevenLabsAudioService() as audio_service:
        response = await audio_service.generate_audio(
            script=script,
            podcast_id="podcast-123",
        )

        if response.success:
            total_cost = (
                script_metrics.cost_estimate +
                response.audio_file.metrics.cost_estimate
            )
            print(f"Total cost: ${total_cost:.4f}")
            return response.audio_file.file_path

asyncio.run(full_pipeline())
```

### FastAPI Integration

```python
from fastapi import Depends, HTTPException
from app.services import get_audio_service, ElevenLabsAudioService

@app.post("/podcasts/{podcast_id}/generate-audio")
async def generate_podcast_audio(
    podcast_id: str,
    audio_service: ElevenLabsAudioService = Depends(get_audio_service),
):
    # Get script from database
    script = await get_podcast_script(podcast_id)

    # Generate audio
    response = await audio_service.generate_audio(
        script=script,
        podcast_id=podcast_id,
    )

    if not response.success:
        raise HTTPException(
            status_code=500,
            detail=response.error_message,
        )

    return {
        "audio_url": response.audio_file.file_url,
        "duration": response.audio_file.duration_seconds,
        "cost": response.audio_file.metrics.cost_estimate,
    }
```

## Configuration

### Voice Mapping

The service maps speakers to ElevenLabs voice IDs. Default voices:

```python
VOICE_MAP = {
    SpeakerType.ALEX: "pNInz6obpgDQGcFmaJgB",   # Adam - Deep male voice
    SpeakerType.SONIA: "EXAVITQu4vr4xnSDxMaL",  # Bella - Professional female voice
}
```

To use different voices:
1. Browse the [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
2. Copy the voice ID
3. Update the `VOICE_MAP` in `audio_service.py`

### Audio Settings

```python
# Audio quality settings
SAMPLE_RATE = 44100  # Hz (CD quality)
CHANNELS = 1         # Mono
BITRATE = 128        # kbps
FORMAT = "mp3"       # Output format

# Break/pause duration
BREAK_DURATION_MS = 1000  # 1 second
```

### Performance Tuning

```python
# Rate limiting
MAX_CONCURRENT_REQUESTS = 3  # Parallel API calls
REQUEST_TIMEOUT = 60.0       # Seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0            # Initial delay in seconds
RETRY_BACKOFF = 2.0          # Exponential backoff multiplier
```

## Data Models

### AudioFile

Complete information about the generated audio file:

```python
class AudioFile(BaseModel):
    podcast_id: str                    # UUID of podcast
    file_path: str                     # Local file path
    file_url: Optional[str]            # Public URL (if uploaded)
    file_size_bytes: int               # File size
    duration_seconds: float            # Audio duration
    format: str                        # File format (mp3)
    sample_rate: int                   # Sample rate (44100)
    channels: int                      # Audio channels (1)
    bitrate_kbps: int                  # Bitrate (128)
    metrics: AudioMetrics              # Generation metrics
    created_at: datetime               # Creation timestamp
```

### AudioMetrics

Detailed metrics about the generation process:

```python
class AudioMetrics(BaseModel):
    total_characters: int              # Total chars processed
    total_latency_ms: int              # Total generation time
    segment_count: int                 # Number of segments
    segment_metrics: List[AudioSegmentMetrics]  # Per-segment details
    cost_estimate: float               # Estimated cost (USD)
    api_calls: int                     # Number of API calls
    retries: int                       # Retry attempts
    model_used: str                    # ElevenLabs model
```

### AudioSegmentMetrics

Metrics for individual segment generation:

```python
class AudioSegmentMetrics(BaseModel):
    segment_index: int                 # Segment position
    speaker: Optional[str]             # Speaker name
    character_count: int               # Characters in segment
    latency_ms: int                    # Generation latency
    voice_id: Optional[str]            # ElevenLabs voice ID
    success: bool                      # Success flag
    error_message: Optional[str]       # Error details if failed
```

## Cost Estimation

### Pricing

ElevenLabs Creator tier (as of 2024):
- **$0.30 per 1,000 characters**

Example costs:
- Short podcast (750 words ~5,000 chars): **~$1.50**
- Medium podcast (1,500 words ~10,000 chars): **~$3.00**
- Long podcast (2,250 words ~15,000 chars): **~$4.50**

### Cost Tracking

The service automatically tracks character count and calculates costs:

```python
response = await audio_service.generate_audio(script, podcast_id)

if response.success:
    metrics = response.audio_file.metrics
    print(f"Characters: {metrics.total_characters}")
    print(f"Cost: ${metrics.cost_estimate:.4f}")
    print(f"Cost per minute: ${metrics.cost_estimate / (response.audio_file.duration_seconds / 60):.4f}")
```

## Error Handling

### Common Errors

1. **API Key Invalid**
```python
ElevenLabsAPIError: API key is invalid or missing
```
Solution: Check your `.env` file has correct `ELEVENLABS_API_KEY`

2. **Rate Limit Exceeded**
```python
ElevenLabsAPIError: Rate limit exceeded
```
Solution: Service automatically retries with backoff. Check your plan limits.

3. **Voice ID Not Found**
```python
ValueError: No voice mapping found for speaker: ALEX
```
Solution: Update `VOICE_MAP` with valid voice IDs from ElevenLabs

4. **Audio Processing Failed**
```python
IOError: Failed to save audio file
```
Solution: Ensure ffmpeg is installed and storage directory is writable

### Graceful Degradation

```python
response = await audio_service.generate_audio(script, podcast_id)

if not response.success:
    logger.error(f"Audio generation failed: {response.error_message}")

    # Fall back to script-only version
    await save_script_only(podcast_id, script)

    # Notify user
    await send_notification(
        user_id,
        "Audio generation failed, script saved"
    )
```

## Performance

### Benchmarks

Typical performance for a 10-minute podcast (~1,500 words):

| Metric | Value |
|--------|-------|
| Segments | 50-80 |
| Characters | ~10,000 |
| API Calls | 50-80 |
| Total Latency | 30-60 seconds |
| File Size | ~10-15 MB |
| Cost | ~$3.00 |

### Optimization Tips

1. **Batch Processing**: Process multiple podcasts in parallel
2. **Caching**: Cache voice IDs and settings
3. **Storage**: Use S3/Cloudinary for production
4. **Monitoring**: Track latency and error rates
5. **Rate Limiting**: Respect API limits to avoid throttling

## Storage Options

### Local Storage (Default)

```python
audio_service = ElevenLabsAudioService(
    storage_path="/tmp/podcasts"
)
```

### S3 Storage (Production)

```python
# After generation, upload to S3
import boto3

async def upload_to_s3(file_path: str, podcast_id: str) -> str:
    s3 = boto3.client('s3')
    key = f"podcasts/{podcast_id}.mp3"

    s3.upload_file(
        file_path,
        'my-podcast-bucket',
        key,
        ExtraArgs={'ContentType': 'audio/mpeg'}
    )

    return f"https://my-podcast-bucket.s3.amazonaws.com/{key}"

# Update audio_file.file_url with S3 URL
file_url = await upload_to_s3(
    response.audio_file.file_path,
    podcast_id
)
```

## Testing

### Unit Tests

```python
import pytest
from app.services.audio_service import ElevenLabsAudioService

@pytest.mark.asyncio
async def test_audio_generation():
    service = ElevenLabsAudioService()

    script = create_test_script()
    response = await service.generate_audio(script, "test-123")

    assert response.success
    assert response.audio_file.file_path.endswith(".mp3")
    assert response.audio_file.duration_seconds > 0
    assert response.audio_file.metrics.cost_estimate > 0
```

### Integration Tests

See `example_audio_usage.py` for complete examples.

## Monitoring

### Metrics to Track

1. **Success Rate**: Percentage of successful generations
2. **Latency**: Average generation time per podcast
3. **Cost**: Daily/monthly spending on ElevenLabs API
4. **Error Rate**: API errors and retries
5. **Queue Depth**: Pending audio generation jobs

### Logging

The service logs detailed information:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Logs include:
# - Segment processing progress
# - API call latency
# - Error details with stack traces
# - Cost estimates
# - Performance metrics
```

## Troubleshooting

### Audio Quality Issues

1. **Robotic Voice**: Increase `stability` in VoiceSettings
2. **Unnatural Pauses**: Adjust `BREAK_DURATION_MS`
3. **Volume Inconsistency**: Enable `use_speaker_boost`
4. **Poor Clarity**: Try different voice IDs from library

### Performance Issues

1. **Slow Generation**: Increase `MAX_CONCURRENT_REQUESTS`
2. **Timeouts**: Increase `REQUEST_TIMEOUT`
3. **Rate Limits**: Decrease `MAX_CONCURRENT_REQUESTS`
4. **High Costs**: Use shorter scripts or adjust voice settings

## Roadmap

Future enhancements:

- [ ] Streaming audio generation
- [ ] Background music support
- [ ] Sound effects integration
- [ ] Multi-language support
- [ ] Voice cloning for custom speakers
- [ ] Real-time audio preview
- [ ] Adaptive quality based on content
- [ ] Advanced audio post-processing

## Support

For issues or questions:
- ElevenLabs API: https://docs.elevenlabs.io/
- Project Issues: [GitHub Issues]
- Documentation: This file

## License

Part of the Personal Podcast Generator project for Prosper AI assessment.
