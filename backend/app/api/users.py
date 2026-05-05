"""
User management endpoints.

This module provides endpoints for:
- Creating new users with preferences
- Retrieving user profiles
- Updating user preferences and settings
"""

import logging
from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserPreferencesRequest,
    UpdateScheduleSettingsRequest,
    UserResponse,
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Create a new user",
    description=(
        "Create a new user with preferences and settings. Users can customize "
        "their interests, content sources, and voice preferences for podcast generation."
    ),
    responses={
        201: {
            "description": "User created successfully",
        },
        422: {
            "description": "Invalid request parameters",
        }
    }
)
async def create_user(
    request: CreateUserRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Create a new user with preferences.

    This endpoint creates a new user record with the specified preferences
    and settings. If no preferences are provided, defaults will be used.

    Args:
        request: User creation parameters
        session: Database session

    Returns:
        UserResponse with created user details
    """
    logger.info(
        f"Creating new user with interests={request.interests}, "
        f"language={request.language}"
    )

    # Build preferences from request
    preferences = User.get_default_preferences()

    if request.interests:
        preferences["interests"] = request.interests

    if request.topics:
        preferences["topics"] = request.topics

    if request.sources:
        preferences["sources"] = request.sources

    preferences["language"] = request.language
    preferences["duration_minutes"] = request.duration_minutes

    if request.voice_settings:
        preferences["voice_settings"] = request.voice_settings

    # Create user with default schedule settings
    user = User(
        preferences=preferences,
        schedule_settings=User.get_default_schedule_settings(),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"User created successfully: user_id={user.id}")

    return UserResponse(
        id=user.id,
        preferences=user.preferences,
        schedule_settings=user.schedule_settings,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description=(
        "Retrieve authenticated user's profile including preferences, schedule settings, "
        "and metadata."
    ),
    responses={
        200: {
            "description": "User retrieved successfully",
        },
        401: {
            "description": "Not authenticated",
        }
    }
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Get current authenticated user's profile.

    This endpoint retrieves complete user information including preferences,
    schedule settings, and timestamps.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        UserResponse with user details
    """
    logger.debug(f"Fetching profile for user_id={current_user.id}")

    return UserResponse(
        id=current_user.id,
        preferences=current_user.preferences,
        schedule_settings=current_user.schedule_settings,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user profile",
    description=(
        "Retrieve complete user profile including preferences, schedule settings, "
        "and metadata."
    ),
    responses={
        200: {
            "description": "User retrieved successfully",
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        }
    }
)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Get user profile by ID.

    This endpoint retrieves complete user information including preferences,
    schedule settings, and timestamps.

    Args:
        user_id: UUID of the user to retrieve
        session: Database session

    Returns:
        UserResponse with user details

    Raises:
        HTTPException: 404 if user not found
    """
    logger.debug(f"Fetching user profile for user_id={user_id}")

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

    logger.debug(f"User retrieved: user_id={user_id}")

    return UserResponse(
        id=user.id,
        preferences=user.preferences,
        schedule_settings=user.schedule_settings,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put(
    "/me/preferences",
    response_model=UserResponse,
    summary="Update user preferences",
    description=(
        "Update authenticated user's preferences and settings. Only provided fields will be updated; "
        "other fields remain unchanged."
    ),
    responses={
        200: {
            "description": "Preferences updated successfully",
        },
        401: {
            "description": "Not authenticated",
        },
        422: {
            "description": "Invalid request parameters",
        }
    }
)
async def update_user_preferences(
    request: UpdateUserPreferencesRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Update authenticated user's preferences.

    This endpoint updates specific user preference fields. Only the fields
    provided in the request will be updated; other fields remain unchanged.
    This allows for partial updates.

    Args:
        request: Preferences to update
        current_user: Current authenticated user
        session: Database session

    Returns:
        UserResponse with updated user details
    """
    logger.info(f"Updating preferences for user_id={current_user.id}")

    user = current_user

    # Update preferences (only provided fields)
    updated = False

    if request.interests is not None:
        user.preferences["interests"] = request.interests
        updated = True
        logger.debug(f"Updated interests for user_id={user.id}")

    if request.topics is not None:
        user.preferences["topics"] = request.topics
        updated = True
        logger.debug(f"Updated topics for user_id={user.id}")

    if request.sources is not None:
        user.preferences["sources"] = request.sources
        updated = True
        logger.debug(f"Updated sources for user_id={user.id}")

    if request.language is not None:
        user.preferences["language"] = request.language
        updated = True
        logger.debug(f"Updated language for user_id={user.id}")

    if request.duration_minutes is not None:
        user.preferences["duration_minutes"] = request.duration_minutes
        updated = True
        logger.debug(f"Updated duration for user_id={user.id}")

    if request.voice_settings is not None:
        user.preferences["voice_settings"] = request.voice_settings
        updated = True
        logger.debug(f"Updated voice_settings for user_id={user.id}")

    if updated:
        # Mark the preferences column as modified for JSONB update
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "preferences")

        await session.commit()
        await session.refresh(user)

        logger.info(f"Preferences updated successfully for user_id={user.id}")
    else:
        logger.debug(f"No preferences changed for user_id={user.id}")

    return UserResponse(
        id=user.id,
        preferences=user.preferences,
        schedule_settings=user.schedule_settings,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put(
    "/me/schedule",
    response_model=UserResponse,
    summary="Update schedule settings",
    description=(
        "Update authenticated user's podcast generation schedule settings. "
        "Only provided fields will be updated; other fields remain unchanged."
    ),
    responses={
        200: {
            "description": "Schedule settings updated successfully",
        },
        401: {
            "description": "Not authenticated",
        },
        422: {
            "description": "Invalid request parameters",
        }
    }
)
async def update_schedule_settings(
    request: UpdateScheduleSettingsRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Update authenticated user's schedule settings.

    This endpoint updates specific schedule setting fields. Only the fields
    provided in the request will be updated; other fields remain unchanged.

    Args:
        request: Schedule settings to update
        current_user: Current authenticated user
        session: Database session

    Returns:
        UserResponse with updated user details
    """
    logger.info(f"Updating schedule settings for user_id={current_user.id}")

    user = current_user

    # Update schedule settings (only provided fields)
    updated = False

    if request.enabled is not None:
        user.schedule_settings["enabled"] = request.enabled
        updated = True
        logger.debug(f"Updated schedule enabled={request.enabled} for user_id={user.id}")

    if request.frequency is not None:
        user.schedule_settings["frequency"] = request.frequency
        updated = True
        logger.debug(f"Updated frequency for user_id={user.id}")

    if request.time is not None:
        user.schedule_settings["time"] = request.time
        updated = True
        logger.debug(f"Updated time for user_id={user.id}")

    if request.timezone is not None:
        user.schedule_settings["timezone"] = request.timezone
        updated = True
        logger.debug(f"Updated timezone for user_id={user.id}")

    if request.days_of_week is not None:
        user.schedule_settings["days_of_week"] = request.days_of_week
        updated = True
        logger.debug(f"Updated days_of_week for user_id={user.id}")

    if updated:
        # Mark the schedule_settings column as modified for JSONB update
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "schedule_settings")

        await session.commit()
        await session.refresh(user)

        logger.info(f"Schedule settings updated successfully for user_id={user.id}")
    else:
        logger.debug(f"No schedule settings changed for user_id={user.id}")

    return UserResponse(
        id=user.id,
        preferences=user.preferences,
        schedule_settings=user.schedule_settings,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description=(
        "Delete a user and all associated data (podcasts, metrics). "
        "This operation is irreversible."
    ),
    responses={
        204: {
            "description": "User deleted successfully",
        },
        404: {
            "description": "User not found",
        }
    }
)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete a user and all associated data.

    This endpoint deletes a user and all related data (podcasts and metrics)
    due to CASCADE delete constraints. This operation is irreversible.

    Args:
        user_id: UUID of the user to delete
        session: Database session

    Raises:
        HTTPException: 404 if user not found
    """
    logger.warning(f"Deletion requested for user_id={user_id}")

    # Fetch user
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found for deletion: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete user (cascade will delete podcasts and metrics)
    await session.delete(user)
    await session.commit()

    logger.warning(
        f"User deleted successfully: user_id={user_id} "
        "(including all associated podcasts and metrics)"
    )
