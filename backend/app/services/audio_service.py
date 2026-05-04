"""
ElevenLabs Audio Generation Service.

Production-grade service for generating high-quality podcast audio using
ElevenLabs Text-to-Speech API with the multilingual_v2 model.

Features:
- Multi-speaker support (Alex and Sonia with distinct voices)
- Smooth speaker transitions
- Break/silence marker handling
- Audio segment combination
- Comprehensive error handling and retries
- Cost tracking and metrics
- Rate limiting protection
- Local storage with optional cloud upload support
"""

import asyncio
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from pydub import AudioSegment

from app.core.config import settings
from app.services.script_service import PodcastScript, ScriptSegment, SpeakerType
from app.schemas.audio import (
    AudioFile,
    AudioGenerationResponse,
    AudioMetrics,
    AudioSegmentMetrics,
    VoiceSettings,
)

logger = logging.getLogger(__name__)


class ElevenLabsAPIError(Exception):
    """Custom exception for ElevenLabs API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class ElevenLabsAudioService:
    """
    Service for generating podcast audio using ElevenLabs TTS API.

    This service handles:
    - Text-to-speech conversion for multiple speakers
    - Audio segment generation and combination
    - Break/silence insertion
    - Cost tracking and metrics
    - Error handling and retries
    - File storage management
    """

    # ElevenLabs API configuration
    BASE_URL = "https://api.elevenlabs.io/v1"
    MODEL = "eleven_multilingual_v2"

    # Voice IDs for podcast speakers (using ElevenLabs pre-made voices)
    # Replace with your desired voice IDs from https://elevenlabs.io/voice-library
    VOICE_MAP = {
        SpeakerType.ALEX: "pNInz6obpgDQGcFmaJgB",  # Adam - Deep male voice
        SpeakerType.SONIA: "EXAVITQu4vr4xnSDxMaL",  # Bella - Professional female voice
    }

    # Pricing (ElevenLabs Creator tier as of 2024)
    COST_PER_1K_CHARS = 0.30  # USD per 1000 characters

    # Audio configuration
    SAMPLE_RATE = 44100  # Hz
    CHANNELS = 1  # Mono
    BITRATE = 128  # kbps
    FORMAT = "mp3"

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF = 2.0  # exponential backoff multiplier

    # Rate limiting
    MAX_CONCURRENT_REQUESTS = 3
    REQUEST_TIMEOUT = 60.0  # seconds

    # Break configuration
    BREAK_DURATION_MS = 1000  # 1 second silence for [BREAK]

    def __init__(
        self,
        api_key: Optional[str] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize ElevenLabsAudioService.

        Args:
            api_key: ElevenLabs API key (defaults to settings.ELEVENLABS_API_KEY)
            storage_path: Path to store generated audio files
        """
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.storage_path = Path(
            storage_path or "/tmp/podcasts"
        )  # Default to /tmp in production use S3/Cloudinary
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # HTTP client for API requests
        self.client: Optional[httpx.AsyncClient] = None

        # Semaphore for rate limiting
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

        logger.info(
            f"ElevenLabsAudioService initialized with storage path: {self.storage_path}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.REQUEST_TIMEOUT),
                limits=httpx.Limits(
                    max_keepalive_connections=10, max_connections=20
                ),
            )

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("ElevenLabsAudioService HTTP client closed")

    def _get_voice_id(self, speaker: SpeakerType) -> str:
        """
        Get ElevenLabs voice ID for a speaker.

        Args:
            speaker: Speaker type (ALEX or SONIA)

        Returns:
            Voice ID string

        Raises:
            ValueError: If speaker is not mapped
        """
        voice_id = self.VOICE_MAP.get(speaker)
        if not voice_id:
            raise ValueError(f"No voice mapping found for speaker: {speaker}")
        return voice_id

    def _calculate_cost(self, character_count: int) -> float:
        """
        Calculate estimated cost for character count.

        Args:
            character_count: Number of characters to process

        Returns:
            Estimated cost in USD
        """
        return round((character_count / 1000) * self.COST_PER_1K_CHARS, 4)

    async def _generate_segment(
        self,
        text: str,
        voice_id: str,
        voice_settings: Optional[VoiceSettings] = None,
        retry_count: int = 0,
    ) -> Tuple[bytes, int]:
        """
        Generate audio for a single text segment using ElevenLabs API.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            voice_settings: Optional voice configuration
            retry_count: Current retry attempt

        Returns:
            Tuple of (audio_bytes, latency_ms)

        Raises:
            ElevenLabsAPIError: If API request fails after retries
        """
        await self._ensure_client()

        # Prepare voice settings
        settings_dict = (
            {
                "stability": voice_settings.stability,
                "similarity_boost": voice_settings.similarity_boost,
                "style": voice_settings.style,
                "use_speaker_boost": voice_settings.use_speaker_boost,
            }
            if voice_settings
            else {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            }
        )

        # Prepare request
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.MODEL,
            "voice_settings": settings_dict,
        }

        start_time = time.perf_counter()

        try:
            async with self._semaphore:  # Rate limiting
                logger.debug(
                    f"Generating audio segment: voice_id={voice_id}, "
                    f"text_length={len(text)}, retry={retry_count}"
                )

                response = await self.client.post(
                    url, json=payload, headers=headers
                )

                # Check for errors
                if response.status_code != 200:
                    error_body = response.text
                    raise ElevenLabsAPIError(
                        message=f"ElevenLabs API error: {response.status_code}",
                        status_code=response.status_code,
                        response_body=error_body,
                    )

                audio_bytes = response.content
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                logger.debug(
                    f"Audio segment generated successfully: "
                    f"size={len(audio_bytes)} bytes, latency={latency_ms}ms"
                )

                return audio_bytes, latency_ms

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            # Retry logic
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (self.RETRY_BACKOFF**retry_count)
                logger.warning(
                    f"Request failed, retrying in {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES}): {e}"
                )
                await asyncio.sleep(delay)
                return await self._generate_segment(
                    text, voice_id, voice_settings, retry_count + 1
                )
            else:
                logger.error(
                    f"Failed to generate audio segment after {self.MAX_RETRIES} retries: {e}"
                )
                raise ElevenLabsAPIError(
                    message=f"Failed after {self.MAX_RETRIES} retries: {str(e)}"
                )

    def _create_silence(self, duration_ms: int) -> AudioSegment:
        """
        Create a silent audio segment.

        Args:
            duration_ms: Duration of silence in milliseconds

        Returns:
            Silent AudioSegment
        """
        return AudioSegment.silent(duration=duration_ms, frame_rate=self.SAMPLE_RATE)

    async def _process_segment(
        self,
        segment: ScriptSegment,
        segment_index: int,
        voice_settings: Optional[Dict[str, VoiceSettings]] = None,
    ) -> Tuple[AudioSegment, AudioSegmentMetrics]:
        """
        Process a single script segment (text or break).

        Args:
            segment: Script segment to process
            segment_index: Index of segment in script
            voice_settings: Optional voice settings per speaker

        Returns:
            Tuple of (AudioSegment, AudioSegmentMetrics)

        Raises:
            Exception: If segment processing fails
        """
        start_time = time.perf_counter()

        try:
            # Handle break markers (pause_after flag in script_service)
            if segment.pause_after:
                silence = self._create_silence(self.BREAK_DURATION_MS)
                # Create audio for the actual segment first
                voice_id = self._get_voice_id(segment.speaker)
                speaker_settings = (
                    voice_settings.get(segment.speaker.value) if voice_settings else None
                )

                # Generate audio from text
                audio_bytes, api_latency_ms = await self._generate_segment(
                    text=segment.text,
                    voice_id=voice_id,
                    voice_settings=speaker_settings,
                )

                # Convert bytes to AudioSegment
                audio_segment = AudioSegment.from_mp3(BytesIO(audio_bytes))
                audio_segment = audio_segment.set_frame_rate(self.SAMPLE_RATE)
                audio_segment = audio_segment.set_channels(self.CHANNELS)

                # Add silence after
                audio_segment = audio_segment + silence

                total_latency_ms = int((time.perf_counter() - start_time) * 1000)

                metrics = AudioSegmentMetrics(
                    segment_index=segment_index,
                    speaker=segment.speaker.value,
                    character_count=len(segment.text),
                    latency_ms=total_latency_ms,
                    voice_id=voice_id,
                    success=True,
                )

                logger.debug(
                    f"Segment with pause processed: speaker={segment.speaker.value}, "
                    f"chars={len(segment.text)}, latency={total_latency_ms}ms"
                )
                return audio_segment, metrics

            # Handle regular speaker segments
            if not segment.speaker:
                raise ValueError(f"Segment {segment_index} has no speaker assigned")

            voice_id = self._get_voice_id(segment.speaker)
            speaker_settings = (
                voice_settings.get(segment.speaker.value) if voice_settings else None
            )

            # Generate audio from text
            audio_bytes, api_latency_ms = await self._generate_segment(
                text=segment.text,
                voice_id=voice_id,
                voice_settings=speaker_settings,
            )

            # Convert bytes to AudioSegment
            audio_segment = AudioSegment.from_mp3(BytesIO(audio_bytes))

            # Ensure consistent format
            audio_segment = audio_segment.set_frame_rate(self.SAMPLE_RATE)
            audio_segment = audio_segment.set_channels(self.CHANNELS)

            total_latency_ms = int((time.perf_counter() - start_time) * 1000)

            metrics = AudioSegmentMetrics(
                segment_index=segment_index,
                speaker=segment.speaker.value,
                character_count=len(segment.text),
                latency_ms=total_latency_ms,
                voice_id=voice_id,
                success=True,
            )

            logger.debug(
                f"Segment processed: speaker={segment.speaker.value}, "
                f"chars={len(segment.text)}, latency={total_latency_ms}ms"
            )

            return audio_segment, metrics

        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                f"Failed to process segment {segment_index}: {e}", exc_info=True
            )

            metrics = AudioSegmentMetrics(
                segment_index=segment_index,
                speaker=segment.speaker.value if segment.speaker else None,
                character_count=len(segment.text),
                latency_ms=latency_ms,
                voice_id=None,
                success=False,
                error_message=str(e),
            )

            raise Exception(f"Segment {segment_index} processing failed: {e}") from e

    def _combine_segments(self, segments: List[AudioSegment]) -> AudioSegment:
        """
        Combine multiple audio segments into a single audio file.

        Args:
            segments: List of AudioSegment objects to combine

        Returns:
            Combined AudioSegment
        """
        if not segments:
            raise ValueError("No audio segments to combine")

        logger.info(f"Combining {len(segments)} audio segments")

        # Combine all segments sequentially
        combined = segments[0]
        for segment in segments[1:]:
            combined += segment

        logger.debug(
            f"Combined audio: duration={len(combined)}ms, "
            f"frame_rate={combined.frame_rate}Hz"
        )

        return combined

    def _save_audio(
        self, audio_data: AudioSegment, podcast_id: str
    ) -> Tuple[str, int]:
        """
        Save audio data to local storage.

        Args:
            audio_data: AudioSegment to save
            podcast_id: Unique podcast identifier

        Returns:
            Tuple of (file_path, file_size_bytes)

        Raises:
            IOError: If file save fails
        """
        file_name = f"{podcast_id}.{self.FORMAT}"
        file_path = self.storage_path / file_name

        try:
            logger.info(f"Saving audio to: {file_path}")

            # Export audio to file
            audio_data.export(
                file_path,
                format=self.FORMAT,
                bitrate=f"{self.BITRATE}k",
                parameters=["-ar", str(self.SAMPLE_RATE)],
            )

            file_size = file_path.stat().st_size

            logger.info(
                f"Audio saved successfully: path={file_path}, size={file_size} bytes"
            )

            return str(file_path), file_size

        except Exception as e:
            logger.error(f"Failed to save audio file: {e}", exc_info=True)
            raise IOError(f"Failed to save audio to {file_path}: {e}") from e

    async def generate_audio(
        self,
        script: PodcastScript,
        podcast_id: str,
        voice_settings: Optional[Dict[str, VoiceSettings]] = None,
    ) -> AudioGenerationResponse:
        """
        Generate complete podcast audio from script.

        This is the main entry point for audio generation. It:
        1. Processes each script segment (speech or break)
        2. Generates audio using ElevenLabs API
        3. Combines segments into final podcast
        4. Saves to local storage
        5. Tracks metrics and costs

        Args:
            script: Complete podcast script with segments
            podcast_id: Unique podcast identifier (UUID)
            voice_settings: Optional custom voice settings per speaker

        Returns:
            AudioGenerationResponse with file info and metrics

        Example:
            >>> service = ElevenLabsAudioService()
            >>> script, metrics = await script_service.generate_script(articles, prefs)
            >>> response = await service.generate_audio(script, podcast_id="abc-123")
            >>> print(f"Audio saved to: {response.audio_file.file_path}")
        """
        start_time = time.perf_counter()

        try:
            await self._ensure_client()

            logger.info(
                f"Starting audio generation for podcast: {podcast_id}, "
                f"segments={len(script.segments)}"
            )

            # Process all segments
            audio_segments: List[AudioSegment] = []
            segment_metrics: List[AudioSegmentMetrics] = []
            total_characters = 0
            total_api_calls = 0
            total_retries = 0

            for i, segment in enumerate(script.segments):
                try:
                    audio_seg, metrics = await self._process_segment(
                        segment=segment,
                        segment_index=i,
                        voice_settings=voice_settings,
                    )

                    audio_segments.append(audio_seg)
                    segment_metrics.append(metrics)

                    if metrics.success and not segment.is_break:
                        total_characters += metrics.character_count
                        total_api_calls += 1

                except Exception as e:
                    logger.error(f"Segment {i} failed: {e}")
                    # Add failed metric
                    segment_metrics.append(
                        AudioSegmentMetrics(
                            segment_index=i,
                            speaker=segment.speaker.value if segment.speaker else None,
                            character_count=len(segment.text) if segment.text else 0,
                            latency_ms=0,
                            success=False,
                            error_message=str(e),
                        )
                    )
                    raise

            # Combine all audio segments
            combined_audio = self._combine_segments(audio_segments)

            # Save to file
            file_path, file_size = self._save_audio(
                combined_audio, podcast_id
            )

            # Calculate metrics
            total_latency_ms = int((time.perf_counter() - start_time) * 1000)
            duration_seconds = len(combined_audio) / 1000.0  # pydub uses milliseconds
            cost_estimate = self._calculate_cost(total_characters)

            metrics = AudioMetrics(
                total_characters=total_characters,
                total_latency_ms=total_latency_ms,
                segment_count=len(script.segments),
                segment_metrics=segment_metrics,
                cost_estimate=cost_estimate,
                api_calls=total_api_calls,
                retries=total_retries,
                model_used=self.MODEL,
            )

            audio_file = AudioFile(
                podcast_id=podcast_id,
                file_path=file_path,
                file_url=None,  # Set this after uploading to CDN/S3
                file_size_bytes=file_size,
                duration_seconds=duration_seconds,
                format=self.FORMAT,
                sample_rate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                bitrate_kbps=self.BITRATE,
                metrics=metrics,
            )

            logger.info(
                f"Audio generation completed: podcast_id={podcast_id}, "
                f"duration={duration_seconds:.1f}s, cost=${cost_estimate:.4f}, "
                f"latency={total_latency_ms}ms"
            )

            return AudioGenerationResponse(success=True, audio_file=audio_file)

        except Exception as e:
            total_latency_ms = int((time.perf_counter() - start_time) * 1000)
            error_message = f"Audio generation failed: {str(e)}"

            logger.error(
                f"Audio generation failed for podcast {podcast_id}: {e}",
                exc_info=True,
            )

            return AudioGenerationResponse(
                success=False,
                audio_file=None,
                error_message=error_message,
            )


# Factory function for dependency injection
async def get_audio_service() -> ElevenLabsAudioService:
    """
    Factory function to get ElevenLabsAudioService instance.

    This can be used as a FastAPI dependency.

    Returns:
        Initialized ElevenLabsAudioService

    Example:
        >>> @app.post("/generate-audio")
        >>> async def generate_audio(
        ...     service: ElevenLabsAudioService = Depends(get_audio_service)
        ... ):
        ...     result = await service.generate_audio(script)
        ...     return result
    """
    service = ElevenLabsAudioService()
    try:
        await service._ensure_client()
        yield service
    finally:
        await service.close()
