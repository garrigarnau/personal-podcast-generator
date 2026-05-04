"""
Pydantic schemas for admin endpoints.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class KPISummary(BaseModel):
    """
    Summary of key performance indicators.

    Attributes:
        total_podcasts: Total number of podcasts generated
        avg_latency_ms: Average generation latency in milliseconds
        total_cost_usd: Total cost across all podcasts
        success_rate: Percentage of successful generations (0-100)
        total_tokens: Total GPT-4 tokens consumed
        total_characters: Total ElevenLabs characters processed
    """

    total_podcasts: int = Field(..., ge=0, description="Total podcasts generated")
    avg_latency_ms: float = Field(..., ge=0, description="Average latency (ms)")
    total_cost_usd: float = Field(..., ge=0, description="Total cost (USD)")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate (%)")
    total_tokens: int = Field(..., ge=0, description="Total GPT-4 tokens")
    total_characters: int = Field(..., ge=0, description="Total ElevenLabs characters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_podcasts": 1234,
                "avg_latency_ms": 45000.5,
                "total_cost_usd": 123.45,
                "success_rate": 98.5,
                "total_tokens": 500000,
                "total_characters": 250000
            }
        }
    )


class DailyVolumeData(BaseModel):
    """
    Daily podcast generation volume data.

    Attributes:
        day: Date of the data point
        total: Total podcasts generated on this day
        completed: Successfully completed podcasts
        failed: Failed podcast generations
        pending: Podcasts still pending/processing
        avg_latency_ms: Average latency for this day
        total_cost_usd: Total cost for this day
    """

    day: date = Field(..., description="Data date")
    total: int = Field(..., ge=0, description="Total podcasts")
    completed: int = Field(..., ge=0, description="Completed podcasts")
    failed: int = Field(..., ge=0, description="Failed podcasts")
    pending: int = Field(..., ge=0, description="Pending/processing podcasts")
    avg_latency_ms: float = Field(..., ge=0, description="Average latency (ms)")
    total_cost_usd: float = Field(..., ge=0, description="Total cost (USD)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day": "2026-05-04",
                "total": 42,
                "completed": 40,
                "failed": 1,
                "pending": 1,
                "avg_latency_ms": 43500.0,
                "total_cost_usd": 4.25
            }
        }
    )


class RecentPodcastItem(BaseModel):
    """
    Brief podcast information for recent podcasts list.

    Attributes:
        id: Podcast identifier
        user_id: User identifier
        status: Current status
        created_at: Creation timestamp
        latency_ms: Generation latency (if available)
        cost_usd: Generation cost (if available)
        error_message: Error message if failed
    """

    id: UUID = Field(..., description="Podcast identifier")
    user_id: UUID = Field(..., description="User identifier")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    latency_ms: Optional[int] = Field(None, description="Generation latency (ms)")
    cost_usd: Optional[float] = Field(None, description="Generation cost (USD)")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "completed",
                "created_at": "2026-05-04T10:00:00Z",
                "latency_ms": 45000,
                "cost_usd": 0.12,
                "error_message": None
            }
        }
    )


class AdminStatsResponse(BaseModel):
    """
    Response schema for admin statistics endpoint.

    Attributes:
        kpis: Key performance indicators summary
        volume_data: Daily volume data for charts (last 30 days)
        recent_podcasts: Most recent podcasts (last 20)
        generated_at: When these stats were generated
    """

    kpis: KPISummary = Field(..., description="KPI summary")
    volume_data: List[DailyVolumeData] = Field(
        ...,
        description="Daily volume data (last 30 days)"
    )
    recent_podcasts: List[RecentPodcastItem] = Field(
        ...,
        description="Recent podcasts (last 20)"
    )
    generated_at: datetime = Field(..., description="Stats generation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kpis": {
                    "total_podcasts": 1234,
                    "avg_latency_ms": 45000.5,
                    "total_cost_usd": 123.45,
                    "success_rate": 98.5,
                    "total_tokens": 500000,
                    "total_characters": 250000
                },
                "volume_data": [
                    {
                        "date": "2026-05-04",
                        "total": 42,
                        "completed": 40,
                        "failed": 1,
                        "pending": 1,
                        "avg_latency_ms": 43500.0,
                        "total_cost_usd": 4.25
                    }
                ],
                "recent_podcasts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "status": "completed",
                        "created_at": "2026-05-04T10:00:00Z",
                        "latency_ms": 45000,
                        "cost_usd": 0.12,
                        "error_message": None
                    }
                ],
                "generated_at": "2026-05-04T12:00:00Z"
            }
        }
    )


class RecentPodcastResponse(BaseModel):
    """
    Response schema for recent podcasts endpoint with pagination.

    Attributes:
        podcasts: List of recent podcasts
        total: Total number of podcasts
        page: Current page number
        page_size: Number of items per page
    """

    podcasts: List[RecentPodcastItem] = Field(..., description="Recent podcasts")
    total: int = Field(..., ge=0, description="Total number of podcasts")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "podcasts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "status": "completed",
                        "created_at": "2026-05-04T10:00:00Z",
                        "latency_ms": 45000,
                        "cost_usd": 0.12,
                        "error_message": None
                    }
                ],
                "total": 500,
                "page": 1,
                "page_size": 20
            }
        }
    )


class DailyMetricsResponse(BaseModel):
    """
    Response schema for daily metrics endpoint.

    Attributes:
        metrics: Daily volume data
        days: Number of days included
        total_podcasts: Total across all days
        total_cost_usd: Total cost across all days
    """

    metrics: List[DailyVolumeData] = Field(..., description="Daily metrics")
    days: int = Field(..., ge=1, description="Number of days included")
    total_podcasts: int = Field(..., ge=0, description="Total podcasts")
    total_cost_usd: float = Field(..., ge=0, description="Total cost (USD)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics": [
                    {
                        "date": "2026-05-04",
                        "total": 42,
                        "completed": 40,
                        "failed": 1,
                        "pending": 1,
                        "avg_latency_ms": 43500.0,
                        "total_cost_usd": 4.25
                    }
                ],
                "days": 30,
                "total_podcasts": 1234,
                "total_cost_usd": 123.45
            }
        }
    )
