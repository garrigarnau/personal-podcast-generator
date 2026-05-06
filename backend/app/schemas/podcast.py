"""
Pydantic schemas for podcast endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class GeneratePodcastRequest(BaseModel):
    """
    Request schema for generating a new podcast.

    Attributes:
        interests: List of topics/interests to focus on (e.g., ["AI", "startups"])
        tone: Podcast tone/style (e.g., "professional", "casual", "educational")
        length: Desired podcast length in minutes (5-30)
        sources: Optional list of specific sources or URLs to include
    """

    interests: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of topics or interests (1-10 items)",
        examples=[["artificial intelligence", "machine learning", "startups"]]
    )

    tone: str = Field(
        default="professional",
        description="Podcast tone/style",
        pattern="^(professional|casual|educational|conversational)$",
        examples=["professional"]
    )

    length: int = Field(
        default=10,
        ge=5,
        le=30,
        description="Desired podcast length in minutes (5-30)",
        examples=[10]
    )

    sources: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Optional specific sources or URLs to include",
        examples=[["https://techcrunch.com", "https://arstechnica.com"]]
    )

    mock_audio: bool = Field(
        default=False,
        description="If true, skip ElevenLabs API calls for testing (generates script only)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "interests": ["artificial intelligence", "machine learning"],
                "tone": "professional",
                "length": 10,
                "sources": ["https://techcrunch.com"],
                "mock_audio": False
            }
        }
    )


class ScriptToAudioRequest(BaseModel):
    """
    Request schema for generating audio from a pre-written script.

    This bypasses news fetching and script generation to save API credits.

    Attributes:
        script_text: Pre-written podcast script with speaker tags
        tone: Script tone for metadata (professional/casual/educational/conversational)
        length: Script length for metadata (short/medium/long)
        mock_audio: If true, skip ElevenLabs API calls (for testing)
    """

    script_text: str = Field(
        ...,
        min_length=50,
        description="Pre-written script with [ALEX] and [SONIA] tags",
        examples=[[
            "[ALEX] (enthusiastic): Welcome to our podcast!\n"
            "[SONIA] (thoughtful): Thanks for having me.\n"
            "[BREAK]\n"
            "[ALEX]: Let's dive in."
        ]]
    )

    tone: str = Field(
        default="professional",
        description="Script tone for metadata",
        pattern="^(professional|casual|educational|conversational)$",
        examples=["professional"]
    )

    length: str = Field(
        default="medium",
        description="Script length category for metadata",
        pattern="^(short|medium|long)$",
        examples=["medium"]
    )

    mock_audio: bool = Field(
        default=False,
        description="If true, skip ElevenLabs API calls for testing"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_text": (
                    "[ALEX] (enthusiastic): Welcome!\n"
                    "[SONIA]: Great to be here.\n"
                    "[BREAK]\n"
                    "[ALEX]: Let's discuss today's topics."
                ),
                "tone": "professional",
                "length": "medium",
                "mock_audio": False
            }
        }
    )


class PodcastResponse(BaseModel):
    """
    Response schema for podcast details.

    Attributes:
        id: Unique podcast identifier
        user_id: User who owns this podcast
        title: AI-generated title for the podcast
        status: Current generation status
        audio_url: URL to generated audio (null if not completed)
        script: Generated podcast script (null if not completed)
        error_message: Error details if failed
        metadata: Additional metadata (topics, sources, etc.)
        created_at: When the podcast was created
        updated_at: When the podcast was last updated
    """

    id: UUID = Field(..., description="Unique podcast identifier")
    user_id: UUID = Field(..., description="User identifier")
    title: Optional[str] = Field(None, description="AI-generated podcast title")
    status: str = Field(..., description="Generation status", examples=["pending"])
    audio_url: Optional[str] = Field(None, description="Audio file URL")
    script: Optional[str] = Field(None, description="Generated podcast script")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    metadata: Optional[str] = Field(
        None,
        description="Additional metadata (JSON)",
        alias="podcast_metadata",
        serialization_alias="metadata"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "completed",
                "audio_url": "https://storage.example.com/podcasts/123.mp3",
                "script": "Welcome to your personalized podcast...",
                "error_message": None,
                "metadata": '{"topics": ["AI", "tech"], "sources": 5}',
                "created_at": "2026-05-04T10:00:00Z",
                "updated_at": "2026-05-04T10:05:00Z"
            }
        }
    )


class PodcastStatusResponse(BaseModel):
    """
    Response schema for polling podcast status.

    Attributes:
        id: Podcast identifier
        title: AI-generated title (available after script generation)
        status: Current generation status
        audio_url: Audio URL if completed
        script: Generated script (available before audio)
        error_message: Error details if failed
        progress: Optional progress percentage (0-100)
        metadata: Optional metadata JSON string (topics, sources, articles, etc.)
    """

    id: UUID = Field(..., description="Podcast identifier")
    title: Optional[str] = Field(None, description="AI-generated podcast title")
    status: str = Field(..., description="Generation status")
    audio_url: Optional[str] = Field(None, description="Audio URL if completed")
    script: Optional[str] = Field(None, description="Generated podcast script")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    progress: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    metadata: Optional[str] = Field(None, description="Metadata JSON string")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "audio_url": None,
                "script": "[ALEX]: Welcome to today's podcast...",
                "error_message": None,
                "progress": 45
            }
        }
    )


class PodcastListResponse(BaseModel):
    """
    Response schema for paginated podcast list.

    Attributes:
        podcasts: List of podcasts
        total: Total number of podcasts
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
    """

    podcasts: List[PodcastResponse] = Field(..., description="List of podcasts")
    total: int = Field(..., ge=0, description="Total number of podcasts")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "podcasts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "status": "completed",
                        "audio_url": "https://storage.example.com/podcasts/123.mp3",
                        "script": "Welcome...",
                        "error_message": None,
                        "metadata": '{"topics": ["AI"]}',
                        "created_at": "2026-05-04T10:00:00Z",
                        "updated_at": "2026-05-04T10:05:00Z"
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 10,
                "total_pages": 5
            }
        }
    )
