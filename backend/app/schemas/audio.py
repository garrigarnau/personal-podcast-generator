"""
Audio service schemas for podcast generation.

This module defines Pydantic models for audio generation requests,
responses, and metadata tracking.

Note: PodcastScript and ScriptSegment are imported from script_service
to avoid duplication and ensure consistency across services.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AudioSegmentMetrics(BaseModel):
    """
    Metrics for a single audio segment generation.

    Attributes:
        segment_index: Index of the segment in the script
        speaker: Speaker name for this segment
        character_count: Number of characters processed
        latency_ms: Time taken to generate this segment
        voice_id: ElevenLabs voice ID used
        success: Whether generation was successful
        error_message: Error details if generation failed
    """

    segment_index: int = Field(..., ge=0)
    speaker: Optional[str] = None
    character_count: int = Field(..., ge=0)
    latency_ms: int = Field(..., ge=0)
    voice_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AudioMetrics(BaseModel):
    """
    Complete metrics for audio generation process.

    Attributes:
        total_characters: Total characters processed by ElevenLabs
        total_latency_ms: Total time for audio generation
        segment_count: Number of segments processed
        segment_metrics: Detailed metrics for each segment
        cost_estimate: Estimated cost in USD
        api_calls: Number of API calls made to ElevenLabs
        retries: Number of retry attempts
        elevenlabs_model: ElevenLabs model identifier
    """

    total_characters: int = Field(..., ge=0)
    total_latency_ms: int = Field(..., ge=0)
    segment_count: int = Field(..., ge=0)
    segment_metrics: List[AudioSegmentMetrics] = Field(default_factory=list)
    cost_estimate: float = Field(..., ge=0)
    api_calls: int = Field(..., ge=0)
    retries: int = Field(default=0, ge=0)
    elevenlabs_model: str = "multilingual_v2"


class AudioFile(BaseModel):
    """
    Generated audio file information.

    Attributes:
        podcast_id: UUID of the podcast
        file_path: Local file path to the generated audio
        file_url: Public URL to access the audio (if uploaded)
        file_size_bytes: Size of the audio file
        duration_seconds: Duration of the audio in seconds
        format: Audio file format (mp3, wav, etc.)
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        bitrate_kbps: Audio bitrate in kilobits per second
        metrics: Detailed generation metrics
        created_at: Timestamp when audio was generated
    """

    podcast_id: str = Field(..., description="UUID of the podcast")
    file_path: str = Field(..., description="Local file path")
    file_url: Optional[str] = Field(None, description="Public URL if uploaded")
    file_size_bytes: int = Field(..., ge=0)
    duration_seconds: float = Field(..., ge=0)
    format: str = Field(default="mp3")
    sample_rate: int = Field(default=44100, ge=8000)
    channels: int = Field(default=1, ge=1, le=2)
    bitrate_kbps: int = Field(default=128, ge=64)
    metrics: AudioMetrics
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "podcast_id": "123e4567-e89b-12d3-a456-426614174000",
                "file_path": "/storage/podcasts/123e4567.mp3",
                "file_url": "https://cdn.example.com/podcasts/123e4567.mp3",
                "file_size_bytes": 1024000,
                "duration_seconds": 180.5,
                "format": "mp3",
                "sample_rate": 44100,
                "channels": 1,
                "bitrate_kbps": 128,
            }
        }
    )


class VoiceSettings(BaseModel):
    """
    Voice configuration for ElevenLabs TTS.

    Attributes:
        stability: Voice stability (0-1)
        similarity_boost: How much to boost similarity to the original voice
        style: Style exaggeration (0-1)
        use_speaker_boost: Whether to boost speaker clarity
    """

    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    use_speaker_boost: bool = Field(default=True)


class AudioGenerationResponse(BaseModel):
    """
    Response from audio generation service.

    Attributes:
        success: Whether generation was successful
        audio_file: Generated audio file information
        error_message: Error details if generation failed
    """

    success: bool
    audio_file: Optional[AudioFile] = None
    error_message: Optional[str] = None
