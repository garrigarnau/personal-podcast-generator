"""
Pydantic schemas for user endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CreateUserRequest(BaseModel):
    """
    Request schema for creating a new user.

    Attributes:
        interests: User's topics of interest
        topics: Specific topics to follow
        sources: Preferred news sources
        language: Preferred language code
        duration_minutes: Default podcast duration
        voice_settings: ElevenLabs voice configuration
    """

    interests: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="User's topics of interest",
        examples=[["technology", "science", "business"]]
    )

    topics: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Specific topics to follow",
        examples=[["AI", "climate change", "startups"]]
    )

    sources: Optional[List[str]] = Field(
        default=None,
        max_length=50,
        description="Preferred news sources",
        examples=[["TechCrunch", "Ars Technica", "The Verge"]]
    )

    language: str = Field(
        default="en",
        pattern="^[a-z]{2}$",
        description="Language code (ISO 639-1)",
        examples=["en"]
    )

    duration_minutes: int = Field(
        default=10,
        ge=5,
        le=30,
        description="Default podcast duration in minutes",
        examples=[10]
    )

    voice_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="ElevenLabs voice configuration",
        examples=[{
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "stability": 0.5,
            "similarity_boost": 0.75
        }]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "interests": ["technology", "science"],
                "topics": ["AI", "machine learning"],
                "sources": ["TechCrunch", "MIT Technology Review"],
                "language": "en",
                "duration_minutes": 10,
                "voice_settings": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
        }
    )


class UpdateUserPreferencesRequest(BaseModel):
    """
    Request schema for updating user preferences.

    Attributes:
        interests: Updated list of interests (optional)
        topics: Updated list of topics (optional)
        sources: Updated list of sources (optional)
        language: Updated language preference (optional)
        duration_minutes: Updated default duration (optional)
        tone: Updated podcast tone (optional)
        voice_settings: Updated voice settings (optional)
    """

    interests: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Updated interests",
    )

    topics: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Updated topics",
    )

    sources: Optional[List[str]] = Field(
        default=None,
        max_length=50,
        description="Updated sources",
    )

    language: Optional[str] = Field(
        default=None,
        pattern="^[a-z]{2}$",
        description="Updated language code",
    )

    duration_minutes: Optional[int] = Field(
        default=None,
        ge=5,
        le=30,
        description="Updated default duration",
    )

    tone: Optional[str] = Field(
        default=None,
        description="Updated podcast tone (professional, casual, educational, conversational)",
    )

    voice_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated voice settings",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "interests": ["AI", "quantum computing"],
                "duration_minutes": 15,
                "tone": "professional",
                "voice_settings": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "stability": 0.6,
                    "similarity_boost": 0.8
                }
            }
        }
    )


class UpdateScheduleSettingsRequest(BaseModel):
    """
    Request schema for updating schedule settings.

    Attributes:
        enabled: Whether automatic scheduling is enabled
        frequency: Scheduling frequency (daily, weekly, etc.)
        time: Time of day to run (HH:MM format)
        timezone: Timezone identifier
        days_of_week: Days of the week to run (1=Monday, 7=Sunday)
    """

    enabled: Optional[bool] = Field(
        default=None,
        description="Enable/disable automatic podcast generation"
    )

    frequency: Optional[str] = Field(
        default=None,
        pattern="^(daily|weekly|custom)$",
        description="Scheduling frequency"
    )

    time: Optional[str] = Field(
        default=None,
        pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
        description="Time in HH:MM format (24-hour)"
    )

    timezone: Optional[str] = Field(
        default=None,
        description="Timezone identifier (e.g., 'America/New_York', 'Europe/London')"
    )

    days_of_week: Optional[List[int]] = Field(
        default=None,
        description="Days of week (1=Monday, 7=Sunday)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "frequency": "daily",
                "time": "08:00",
                "timezone": "America/New_York",
                "days_of_week": [1, 2, 3, 4, 5]
            }
        }
    )


class UserResponse(BaseModel):
    """
    Response schema for user details.

    Attributes:
        id: Unique user identifier
        preferences: User preferences (interests, settings, etc.)
        schedule_settings: Podcast scheduling configuration
        created_at: When the user was created
        updated_at: When the user was last updated
    """

    id: UUID = Field(..., description="Unique user identifier")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    schedule_settings: Dict[str, Any] = Field(..., description="Schedule settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "preferences": {
                    "interests": ["technology", "science"],
                    "topics": ["AI", "climate change"],
                    "sources": ["TechCrunch"],
                    "language": "en",
                    "duration_minutes": 10,
                    "voice_settings": {
                        "voice_id": "21m00Tcm4TlvDq8ikWAM",
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                "schedule_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "time": "08:00",
                    "timezone": "UTC",
                    "days_of_week": [1, 2, 3, 4, 5]
                },
                "created_at": "2026-05-04T10:00:00Z",
                "updated_at": "2026-05-04T10:00:00Z"
            }
        }
    )
