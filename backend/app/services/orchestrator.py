"""
Podcast Generation Orchestrator.

This module coordinates the entire podcast generation pipeline, managing the async workflow
from news fetching through audio generation to final storage. It provides production-grade
reliability with comprehensive error handling, metrics tracking, and database state management.

Key Features:
- Async-first architecture for high performance
- Comprehensive database status tracking (Pending → Processing → Completed/Failed)
- Detailed metrics collection for each pipeline stage
- Graceful error handling with partial result preservation
- Structured logging for full observability
- Integration with FastAPI BackgroundTasks

Architecture:
    News Service → Script Service → Audio Service → Storage
         ↓              ↓                ↓             ↓
    Update Status → Save Script → Save Audio → Final Metrics

Example:
    >>> orchestrator = PodcastOrchestrator(db_session)
    >>> await orchestrator.generate_podcast_async(
    ...     podcast_id="abc-123",
    ...     user_id="user-456",
    ...     interests=["AI", "Technology"],
    ...     preferences={"tone": "casual", "length": "medium"}
    ... )
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.podcast import Podcast, PodcastStatus
from app.models.metrics import Metrics
from app.services.news_service import FirecrawlNewsService, FetchedNewsArticle
from app.services.script_service import (
    ScriptGeneratorService,
    NewsArticle,
    PodcastScript,
    GenerationMetrics as ScriptMetrics,
)
from app.services.audio_service import ElevenLabsAudioService, AudioGenerationResponse


# Configure logging
logger = logging.getLogger(__name__)


class PodcastGenerationError(Exception):
    """Custom exception for podcast generation errors."""

    def __init__(self, stage: str, message: str, original_error: Optional[Exception] = None):
        self.stage = stage
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{stage}] {message}")


class PodcastOrchestrator:
    """
    Orchestrator for the complete podcast generation pipeline.

    This class manages the end-to-end workflow of podcast generation,
    coordinating between multiple services and maintaining database state.

    Responsibilities:
    - Coordinate News, Script, and Audio services
    - Track pipeline progress in database
    - Collect and aggregate metrics from all stages
    - Handle errors gracefully with appropriate rollback
    - Log all operations for observability
    - Save final results to database

    Stages:
    1. News Fetching: Retrieve relevant articles based on interests
    2. Script Generation: Create conversational podcast script from articles
    3. Audio Generation: Convert script to speech with multiple voices
    4. Storage & Finalization: Save audio and metrics to database

    Attributes:
        db: Async database session
        news_service: Service for fetching news articles
        script_service: Service for generating podcast scripts
        audio_service: Service for generating audio from scripts
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the PodcastOrchestrator.

        Args:
            db: Async SQLAlchemy database session
        """
        self.db = db
        self.news_service = FirecrawlNewsService()
        self.script_service = ScriptGeneratorService()
        self.audio_service = ElevenLabsAudioService()

        logger.info("PodcastOrchestrator initialized")

    async def generate_podcast_async(
        self,
        podcast_id: str,
        user_id: str,
        interests: List[str],
        preferences: Dict[str, Any],
    ) -> None:
        """
        Generate a complete podcast asynchronously.

        This is the main orchestration method that coordinates the entire pipeline.
        It updates the database status at each stage and handles errors gracefully.

        Pipeline Flow:
        1. Mark podcast as "processing"
        2. Fetch news articles based on interests
        3. Generate conversational script from articles
        4. Generate audio from script
        5. Store audio file and metadata
        6. Save comprehensive metrics
        7. Mark podcast as "completed" or "failed"

        Args:
            podcast_id: UUID of the podcast record to process
            user_id: UUID of the user requesting the podcast
            interests: List of user interests/topics for news filtering
            preferences: User preferences (tone, length, voice settings, etc.)

        Raises:
            PodcastGenerationError: If any stage fails critically

        Example:
            >>> orchestrator = PodcastOrchestrator(db)
            >>> await orchestrator.generate_podcast_async(
            ...     podcast_id="550e8400-e29b-41d4-a716-446655440000",
            ...     user_id="user-123",
            ...     interests=["technology", "AI", "startups"],
            ...     preferences={
            ...         "tone": "casual",
            ...         "length": "medium",
            ...         "max_articles": 5,
            ...         "days_back": 7
            ...     }
            ... )
        """
        start_time = datetime.utcnow()

        # Initialize metrics tracking
        stage_metrics = {
            "news_fetch_ms": 0,
            "script_generation_ms": 0,
            "audio_generation_ms": 0,
            "tokens_used": 0,
            "elevenlabs_characters": 0,
            "cost_estimate": 0.0,
        }

        logger.info(
            f"Starting podcast generation: podcast_id={podcast_id}, "
            f"user_id={user_id}, interests={interests}"
        )

        try:
            # Load podcast from database
            podcast = await self._load_podcast(podcast_id)
            if not podcast:
                raise PodcastGenerationError(
                    stage="initialization",
                    message=f"Podcast {podcast_id} not found in database",
                )

            # Stage 1: Mark as processing
            await self._update_status(podcast, PodcastStatus.PROCESSING)
            logger.info(f"[{podcast_id}] Status updated to PROCESSING")

            # Stage 2: Fetch news articles
            logger.info(f"[{podcast_id}] Stage 1/3: Fetching news articles...")
            articles, news_latency = await self._fetch_news(
                interests=interests,
                preferences=preferences,
            )
            stage_metrics["news_fetch_ms"] = news_latency
            logger.info(
                f"[{podcast_id}] Fetched {len(articles)} articles in {news_latency}ms"
            )

            if not articles:
                raise PodcastGenerationError(
                    stage="news_fetch",
                    message="No relevant articles found for given interests",
                )

            # Stage 3: Generate script
            logger.info(f"[{podcast_id}] Stage 2/3: Generating podcast script...")
            script, script_metrics, script_latency = await self._generate_script(
                articles=articles,
                preferences=preferences,
            )
            stage_metrics["script_generation_ms"] = script_latency
            stage_metrics["tokens_used"] = script_metrics.tokens_used
            stage_metrics["cost_estimate"] += script_metrics.cost_estimate

            logger.info(
                f"[{podcast_id}] Script generated: {script.total_word_count} words, "
                f"{script_metrics.tokens_used} tokens, {script_latency}ms"
            )

            # Save script to podcast
            podcast.script = script.get_full_text()
            podcast.metadata = json.dumps({
                "topics": script.topics_covered,
                "sources": script.sources_cited,
                "word_count": script.total_word_count,
                "estimated_duration": script.estimated_duration_seconds,
                "tone": script.tone.value,
                "length": script.length.value,
            })
            await self.db.flush()

            # Stage 4: Generate audio
            logger.info(f"[{podcast_id}] Stage 3/3: Generating podcast audio...")
            audio_response, audio_latency = await self._generate_audio(
                script=script,
                podcast_id=podcast_id,
                preferences=preferences,
            )
            stage_metrics["audio_generation_ms"] = audio_latency

            if not audio_response.success or not audio_response.audio_file:
                raise PodcastGenerationError(
                    stage="audio_generation",
                    message=audio_response.error_message or "Audio generation failed",
                )

            stage_metrics["elevenlabs_characters"] = audio_response.audio_file.metrics.total_characters
            stage_metrics["cost_estimate"] += audio_response.audio_file.metrics.cost_estimate

            logger.info(
                f"[{podcast_id}] Audio generated: {audio_response.audio_file.duration_seconds:.1f}s, "
                f"{audio_response.audio_file.file_size_bytes} bytes, {audio_latency}ms"
            )

            # Stage 5: Save audio path and mark as completed
            podcast.audio_url = audio_response.audio_file.file_path
            await self._update_status(podcast, PodcastStatus.COMPLETED)

            # Stage 6: Save comprehensive metrics
            total_latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._save_metrics(
                podcast_id=podcast_id,
                stage_metrics=stage_metrics,
                total_latency_ms=total_latency,
            )

            # Commit all changes
            await self.db.commit()

            logger.info(
                f"[{podcast_id}] Podcast generation completed successfully! "
                f"Total time: {total_latency}ms, Cost: ${stage_metrics['cost_estimate']:.4f}"
            )

        except PodcastGenerationError as e:
            # Handle known errors
            logger.error(
                f"[{podcast_id}] Podcast generation failed at stage '{e.stage}': {e.message}",
                exc_info=True,
            )
            await self._handle_failure(
                podcast_id=podcast_id,
                error_message=f"[{e.stage}] {e.message}",
                stage_metrics=stage_metrics,
            )
            raise

        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"[{podcast_id}] Unexpected error during podcast generation: {e}",
                exc_info=True,
            )
            await self._handle_failure(
                podcast_id=podcast_id,
                error_message=f"Unexpected error: {str(e)}",
                stage_metrics=stage_metrics,
            )
            raise PodcastGenerationError(
                stage="unknown",
                message=str(e),
                original_error=e,
            )

        finally:
            # Cleanup resources
            await self._cleanup()

    async def _load_podcast(self, podcast_id: str) -> Optional[Podcast]:
        """
        Load podcast from database by ID.

        Args:
            podcast_id: UUID of the podcast

        Returns:
            Podcast instance or None if not found
        """
        try:
            uuid_obj = UUID(podcast_id)
            result = await self.db.execute(
                select(Podcast).where(Podcast.id == uuid_obj)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to load podcast {podcast_id}: {e}")
            return None

    async def _update_status(
        self,
        podcast: Podcast,
        status: PodcastStatus,
    ) -> None:
        """
        Update podcast status in database.

        Args:
            podcast: Podcast instance to update
            status: New status to set

        Raises:
            Exception: If database update fails
        """
        try:
            podcast.status = status
            podcast.updated_at = datetime.utcnow()
            await self.db.flush()
            logger.debug(f"Podcast {podcast.id} status updated to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update podcast status: {e}")
            raise

    async def _fetch_news(
        self,
        interests: List[str],
        preferences: Dict[str, Any],
    ) -> tuple[List[FetchedNewsArticle], int]:
        """
        Fetch news articles based on user interests.

        Args:
            interests: List of user interests/topics
            preferences: User preferences (max_articles, days_back, etc.)

        Returns:
            Tuple of (articles_list, latency_ms)

        Raises:
            PodcastGenerationError: If news fetching fails
        """
        start_time = datetime.utcnow()

        try:
            max_articles = preferences.get("max_articles", 5)
            days_back = preferences.get("days_back", 7)
            min_relevance = preferences.get("min_relevance_score", 0.3)

            articles = await self.news_service.fetch_news(
                interests=interests,
                max_articles=max_articles,
                days_back=days_back,
                min_relevance_score=min_relevance,
            )

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return articles, latency_ms

        except Exception as e:
            logger.error(f"News fetching failed: {e}", exc_info=True)
            raise PodcastGenerationError(
                stage="news_fetch",
                message=f"Failed to fetch news articles: {str(e)}",
                original_error=e,
            )

    async def _generate_script(
        self,
        articles: List[FetchedNewsArticle],
        preferences: Dict[str, Any],
    ) -> tuple[PodcastScript, ScriptMetrics, int]:
        """
        Generate podcast script from news articles.

        Args:
            articles: List of fetched news articles
            preferences: User preferences (tone, length, etc.)

        Returns:
            Tuple of (script, metrics, latency_ms)

        Raises:
            PodcastGenerationError: If script generation fails
        """
        start_time = datetime.utcnow()

        try:
            # Convert FetchedNewsArticle to NewsArticle for script service
            news_articles = [
                NewsArticle(
                    title=article.title,
                    summary=article.summary or article.content[:200],
                    content=article.content,
                    source=article.source,
                    url=str(article.url),
                    published_at=article.published_date,
                    category=article.topics[0] if article.topics else None,
                )
                for article in articles
            ]

            script, metrics = await self.script_service.generate_script(
                news_articles=news_articles,
                preferences=preferences,
            )

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return script, metrics, latency_ms

        except Exception as e:
            logger.error(f"Script generation failed: {e}", exc_info=True)
            raise PodcastGenerationError(
                stage="script_generation",
                message=f"Failed to generate script: {str(e)}",
                original_error=e,
            )

    async def _generate_audio(
        self,
        script: PodcastScript,
        podcast_id: str,
        preferences: Dict[str, Any],
    ) -> tuple[AudioGenerationResponse, int]:
        """
        Generate audio from podcast script.

        Args:
            script: Generated podcast script
            podcast_id: UUID of the podcast
            preferences: User preferences (voice settings, etc.)

        Returns:
            Tuple of (audio_response, latency_ms)

        Raises:
            PodcastGenerationError: If audio generation fails
        """
        start_time = datetime.utcnow()

        try:
            # Extract voice settings from preferences if provided
            voice_settings = preferences.get("voice_settings")

            response = await self.audio_service.generate_audio(
                script=script,
                podcast_id=podcast_id,
                voice_settings=voice_settings,
            )

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return response, latency_ms

        except Exception as e:
            logger.error(f"Audio generation failed: {e}", exc_info=True)
            raise PodcastGenerationError(
                stage="audio_generation",
                message=f"Failed to generate audio: {str(e)}",
                original_error=e,
            )

    async def _save_metrics(
        self,
        podcast_id: str,
        stage_metrics: Dict[str, Any],
        total_latency_ms: int,
    ) -> None:
        """
        Save comprehensive metrics to database.

        Args:
            podcast_id: UUID of the podcast
            stage_metrics: Metrics collected from all stages
            total_latency_ms: Total end-to-end latency

        Raises:
            Exception: If metrics save fails
        """
        try:
            uuid_obj = UUID(podcast_id)

            # Check if metrics already exist
            result = await self.db.execute(
                select(Metrics).where(Metrics.podcast_id == uuid_obj)
            )
            metrics = result.scalar_one_or_none()

            if metrics:
                # Update existing metrics
                metrics.tokens_used = stage_metrics.get("tokens_used", 0)
                metrics.elevenlabs_characters = stage_metrics.get("elevenlabs_characters", 0)
                metrics.latency_ms = total_latency_ms
                metrics.news_fetch_ms = stage_metrics.get("news_fetch_ms", 0)
                metrics.script_generation_ms = stage_metrics.get("script_generation_ms", 0)
                metrics.audio_generation_ms = stage_metrics.get("audio_generation_ms", 0)
                metrics.cost_estimate = stage_metrics.get("cost_estimate", 0.0)
                metrics.update_cost_estimate()
            else:
                # Create new metrics
                metrics = Metrics(
                    podcast_id=uuid_obj,
                    tokens_used=stage_metrics.get("tokens_used", 0),
                    elevenlabs_characters=stage_metrics.get("elevenlabs_characters", 0),
                    latency_ms=total_latency_ms,
                    news_fetch_ms=stage_metrics.get("news_fetch_ms", 0),
                    script_generation_ms=stage_metrics.get("script_generation_ms", 0),
                    audio_generation_ms=stage_metrics.get("audio_generation_ms", 0),
                    cost_estimate=stage_metrics.get("cost_estimate", 0.0),
                )
                self.db.add(metrics)

            await self.db.flush()

            logger.info(
                f"Metrics saved for podcast {podcast_id}: "
                f"tokens={metrics.tokens_used}, chars={metrics.elevenlabs_characters}, "
                f"cost=${metrics.cost_estimate:.4f}"
            )

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}", exc_info=True)
            # Don't raise - metrics failure shouldn't fail the entire generation

    async def _handle_failure(
        self,
        podcast_id: str,
        error_message: str,
        stage_metrics: Dict[str, Any],
    ) -> None:
        """
        Handle podcast generation failure.

        Updates podcast status to FAILED, saves error message, and attempts
        to save partial metrics.

        Args:
            podcast_id: UUID of the podcast
            error_message: Description of the error
            stage_metrics: Partial metrics collected before failure
        """
        try:
            podcast = await self._load_podcast(podcast_id)
            if podcast:
                podcast.status = PodcastStatus.FAILED
                podcast.error_message = error_message[:1000]  # Truncate if too long
                podcast.updated_at = datetime.utcnow()

                # Try to save partial metrics
                if any(stage_metrics.values()):
                    await self._save_metrics(
                        podcast_id=podcast_id,
                        stage_metrics=stage_metrics,
                        total_latency_ms=stage_metrics.get("total_latency_ms", 0),
                    )

                await self.db.commit()
                logger.info(f"Podcast {podcast_id} marked as FAILED")
            else:
                logger.error(f"Could not load podcast {podcast_id} to mark as failed")

        except Exception as e:
            logger.error(f"Failed to handle failure for podcast {podcast_id}: {e}")
            await self.db.rollback()

    async def _cleanup(self) -> None:
        """
        Cleanup resources after podcast generation.

        Closes service connections and releases resources.
        """
        try:
            # Close audio service HTTP client
            if self.audio_service.client:
                await self.audio_service.close()

            logger.debug("Orchestrator cleanup completed")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


# ============================================================================
# Helper Functions for FastAPI Integration
# ============================================================================


async def trigger_podcast_generation(
    podcast_id: str,
    user_id: str,
    interests: List[str],
    preferences: Dict[str, Any],
    db: AsyncSession,
) -> None:
    """
    Trigger podcast generation as a background task.

    This function is designed to work with FastAPI's BackgroundTasks.
    It creates a new orchestrator instance and runs the generation pipeline.

    Args:
        podcast_id: UUID of the podcast to generate
        user_id: UUID of the user requesting generation
        interests: List of user interests for news filtering
        preferences: User preferences for generation
        db: Async database session

    Example:
        >>> from fastapi import BackgroundTasks
        >>>
        >>> @app.post("/podcasts/generate")
        >>> async def generate_podcast(
        ...     request: GenerateRequest,
        ...     background_tasks: BackgroundTasks,
        ...     db: AsyncSession = Depends(get_session)
        ... ):
        ...     # Create podcast record
        ...     podcast = Podcast(user_id=request.user_id, status=PodcastStatus.PENDING)
        ...     db.add(podcast)
        ...     await db.commit()
        ...
        ...     # Trigger background generation
        ...     background_tasks.add_task(
        ...         trigger_podcast_generation,
        ...         podcast_id=str(podcast.id),
        ...         user_id=request.user_id,
        ...         interests=request.interests,
        ...         preferences=request.preferences,
        ...         db=db
        ...     )
        ...
        ...     return {"podcast_id": str(podcast.id), "status": "pending"}
    """
    logger.info(
        f"Background task started for podcast {podcast_id}"
    )

    try:
        orchestrator = PodcastOrchestrator(db)
        await orchestrator.generate_podcast_async(
            podcast_id=podcast_id,
            user_id=user_id,
            interests=interests,
            preferences=preferences,
        )
        logger.info(f"Background task completed for podcast {podcast_id}")

    except Exception as e:
        logger.error(
            f"Background task failed for podcast {podcast_id}: {e}",
            exc_info=True,
        )
        # Error is already handled in orchestrator, just log here
