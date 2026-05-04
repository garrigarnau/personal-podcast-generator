"""
Podcast generation and management endpoints.

This module provides endpoints for:
- Generating new podcasts (async)
- Polling podcast status
- Retrieving podcast details
- Listing user podcasts with pagination
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_session
from app.core.auth import get_current_active_user
from app.models.podcast import Podcast, PodcastStatus
from app.models.user import User
from app.schemas.podcast import (
    GeneratePodcastRequest,
    PodcastResponse,
    PodcastListResponse,
    PodcastStatusResponse,
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/podcasts", tags=["podcasts"])


async def generate_podcast_background(
    podcast_id: UUID,
    user_id: UUID,
    request_data: GeneratePodcastRequest,
    session: AsyncSession,
) -> None:
    """
    Background task to generate podcast asynchronously using the orchestrator.

    This function integrates with the PodcastOrchestrator to manage the complete
    podcast generation pipeline:
    1. Fetch news articles using Firecrawl based on interests
    2. Generate script using GPT-4o
    3. Convert script to audio using ElevenLabs
    4. Store audio file and save metrics
    5. Update podcast record with audio_url and status

    Args:
        podcast_id: ID of the podcast to generate
        user_id: ID of the user requesting the podcast
        request_data: Generation parameters (interests, tone, length, etc.)
        session: Database session for the background task
    """
    from app.services.orchestrator import trigger_podcast_generation

    logger.info(
        f"Starting podcast generation for podcast_id={podcast_id}, user_id={user_id}"
    )

    # Build preferences dictionary from request
    preferences = {
        "tone": request_data.tone,
        "length": request_data.length,
        "max_articles": 5,  # Default to 5 articles
        "days_back": 7,  # Default to last 7 days
        "min_relevance_score": 0.3,  # Minimum relevance threshold
    }

    # Add sources if specified
    if request_data.sources:
        preferences["sources"] = request_data.sources

    try:
        # Use the orchestrator to handle the complete pipeline
        await trigger_podcast_generation(
            podcast_id=str(podcast_id),
            user_id=str(user_id),
            interests=request_data.interests,
            preferences=preferences,
            db=session,
        )

        logger.info(
            f"Podcast generation completed successfully for podcast_id={podcast_id}"
        )

    except Exception as e:
        logger.error(
            f"Podcast generation failed for podcast_id={podcast_id}: {str(e)}",
            exc_info=True
        )
        # Error handling is managed by the orchestrator


@router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PodcastStatusResponse,
    summary="Generate a new podcast",
    description=(
        "Triggers asynchronous podcast generation. Returns immediately with a "
        "podcast ID that can be used to poll status. The podcast will be generated "
        "based on the user's interests and preferences."
    ),
    responses={
        202: {
            "description": "Podcast generation started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "pending",
                        "audio_url": None,
                        "error_message": None,
                        "progress": 0
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        },
        422: {
            "description": "Invalid request parameters",
        }
    }
)
async def generate_podcast(
    user_id: UUID,
    request: GeneratePodcastRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> PodcastStatusResponse:
    """
    Generate a new personalized podcast.

    This endpoint triggers asynchronous podcast generation and returns immediately
    with a 202 Accepted status. The caller should poll the status endpoint to
    check when the podcast is ready.

    Args:
        user_id: UUID of the user requesting the podcast
        request: Podcast generation parameters
        background_tasks: FastAPI background tasks manager
        session: Database session

    Returns:
        PodcastStatusResponse with podcast ID and initial status

    Raises:
        HTTPException: 404 if user not found
    """
    logger.info(
        f"Received podcast generation request for user_id={user_id}, "
        f"interests={request.interests}, tone={request.tone}, length={request.length}"
    )

    # Verify user exists
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create podcast record with pending status
    podcast = Podcast(
        user_id=user_id,
        status=PodcastStatus.PENDING,
        metadata=str({
            "interests": request.interests,
            "tone": request.tone,
            "length": request.length,
            "sources": request.sources,
        })
    )

    session.add(podcast)
    await session.commit()
    await session.refresh(podcast)

    logger.info(
        f"Created podcast record: podcast_id={podcast.id}, user_id={user_id}, "
        f"status={podcast.status.value}"
    )

    # Trigger background generation with orchestrator
    # Note: We need to create a new session for the background task
    # to avoid issues with session lifecycle
    background_tasks.add_task(
        generate_podcast_background,
        podcast.id,
        user_id,
        request,
        session
    )

    return PodcastStatusResponse(
        id=podcast.id,
        status=podcast.status.value,
        audio_url=None,
        error_message=None,
        progress=0
    )


@router.get(
    "/{podcast_id}",
    response_model=PodcastResponse,
    summary="Get podcast details",
    description=(
        "Retrieve complete details for a specific podcast, including status, "
        "audio URL (if completed), script, and metadata."
    ),
    responses={
        200: {
            "description": "Podcast details retrieved successfully",
        },
        404: {
            "description": "Podcast not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Podcast not found"}
                }
            }
        }
    }
)
async def get_podcast(
    podcast_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PodcastResponse:
    """
    Get detailed information about a podcast.

    This endpoint returns complete podcast details including status, audio URL,
    script, and metadata. Use this endpoint to check if a podcast is ready.

    Args:
        podcast_id: UUID of the podcast to retrieve
        session: Database session

    Returns:
        PodcastResponse with complete podcast details

    Raises:
        HTTPException: 404 if podcast not found
    """
    logger.debug(f"Fetching podcast details for podcast_id={podcast_id}")

    result = await session.execute(
        select(Podcast).where(Podcast.id == podcast_id)
    )
    podcast = result.scalar_one_or_none()

    if not podcast:
        logger.warning(f"Podcast not found: podcast_id={podcast_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    logger.debug(
        f"Podcast retrieved: podcast_id={podcast_id}, status={podcast.status.value}"
    )

    return PodcastResponse(
        id=podcast.id,
        user_id=podcast.user_id,
        status=podcast.status.value,
        audio_url=podcast.audio_url,
        script=podcast.script,
        error_message=podcast.error_message,
        metadata=podcast.metadata,
        created_at=podcast.created_at,
        updated_at=podcast.updated_at,
    )


@router.get(
    "/{podcast_id}/status",
    response_model=PodcastStatusResponse,
    summary="Poll podcast status",
    description=(
        "Lightweight endpoint for polling podcast generation status. Returns "
        "current status, audio URL (if completed), and progress information."
    ),
    responses={
        200: {
            "description": "Status retrieved successfully",
        },
        404: {
            "description": "Podcast not found",
        }
    }
)
async def get_podcast_status(
    podcast_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PodcastStatusResponse:
    """
    Get current status of podcast generation.

    This is a lightweight endpoint optimized for polling. It returns only
    essential status information without the full podcast details.

    Args:
        podcast_id: UUID of the podcast to check
        session: Database session

    Returns:
        PodcastStatusResponse with current status and progress

    Raises:
        HTTPException: 404 if podcast not found
    """
    logger.debug(f"Polling podcast status for podcast_id={podcast_id}")

    result = await session.execute(
        select(Podcast).where(Podcast.id == podcast_id)
    )
    podcast = result.scalar_one_or_none()

    if not podcast:
        logger.warning(f"Podcast not found for status check: podcast_id={podcast_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    # Calculate progress based on status
    progress = 0
    if podcast.status == PodcastStatus.PENDING:
        progress = 0
    elif podcast.status == PodcastStatus.PROCESSING:
        progress = 50  # Placeholder - will be more granular with actual pipeline
    elif podcast.status == PodcastStatus.COMPLETED:
        progress = 100
    elif podcast.status == PodcastStatus.FAILED:
        progress = 0

    return PodcastStatusResponse(
        id=podcast.id,
        status=podcast.status.value,
        audio_url=podcast.audio_url,
        error_message=podcast.error_message,
        progress=progress
    )


@router.get(
    "/",
    response_model=PodcastListResponse,
    summary="List user's podcasts",
    description=(
        "Retrieve a paginated list of podcasts for the authenticated user. Supports "
        "filtering by status and ordering by creation date."
    ),
    responses={
        200: {
            "description": "Podcasts retrieved successfully",
        },
        401: {
            "description": "Not authenticated",
        }
    }
)
async def list_podcasts(
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> PodcastListResponse:
    """
    List podcasts for the authenticated user with pagination.

    This endpoint returns a paginated list of podcasts with optional status
    filtering. Results are ordered by creation date (newest first).

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        status_filter: Optional status filter (pending, processing, completed, failed)
        current_user: Current authenticated user
        session: Database session

    Returns:
        PodcastListResponse with paginated podcast list
    """
    logger.info(
        f"Listing podcasts for user_id={current_user.id}, page={page}, "
        f"page_size={page_size}, status_filter={status_filter}"
    )

    # Validate pagination parameters
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page must be >= 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page size must be between 1 and 100"
        )

    # Build query with optional status filter
    query = select(Podcast).where(Podcast.user_id == current_user.id)

    if status_filter:
        try:
            status_enum = PodcastStatus(status_filter)
            query = query.where(Podcast.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {status_filter}"
            )

    # Get total count
    count_query = select(func.count()).select_from(Podcast).where(
        and_(
            Podcast.user_id == current_user.id,
            Podcast.status == status_enum if status_filter else True
        )
    )
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Podcast.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    podcasts = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    logger.info(
        f"Retrieved {len(podcasts)} podcasts for user_id={current_user.id}, "
        f"total={total}, page={page}/{total_pages}"
    )

    return PodcastListResponse(
        podcasts=[
            PodcastResponse(
                id=p.id,
                user_id=p.user_id,
                status=p.status.value,
                audio_url=p.audio_url,
                script=p.script,
                error_message=p.error_message,
                metadata=p.metadata,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in podcasts
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
