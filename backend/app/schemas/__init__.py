"""
Pydantic schemas for request/response validation.
"""

from app.schemas.podcast import (
    GeneratePodcastRequest,
    PodcastResponse,
    PodcastListResponse,
    PodcastStatusResponse,
)
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserPreferencesRequest,
    UserResponse,
)
from app.schemas.admin import (
    AdminStatsResponse,
    RecentPodcastResponse,
    DailyMetricsResponse,
)
from app.schemas.audio import (
    AudioFile,
    AudioGenerationResponse,
    AudioMetrics,
    AudioSegmentMetrics,
    VoiceSettings,
)

__all__ = [
    "GeneratePodcastRequest",
    "PodcastResponse",
    "PodcastListResponse",
    "PodcastStatusResponse",
    "CreateUserRequest",
    "UpdateUserPreferencesRequest",
    "UserResponse",
    "AdminStatsResponse",
    "RecentPodcastResponse",
    "DailyMetricsResponse",
    "AudioFile",
    "AudioGenerationResponse",
    "AudioMetrics",
    "AudioSegmentMetrics",
    "VoiceSettings",
]
