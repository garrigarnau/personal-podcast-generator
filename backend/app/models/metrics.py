"""
Metrics model for tracking podcast generation performance and costs.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Float,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Metrics(Base):
    """
    Metrics model for tracking podcast generation performance and costs.

    Attributes:
        id: Unique metrics identifier (UUID)
        podcast_id: Foreign key to podcasts table (one-to-one)
        tokens_used: Number of tokens consumed by GPT-4o
        elevenlabs_characters: Number of characters processed by ElevenLabs
        latency_ms: Total latency in milliseconds for podcast generation
        cost_estimate: Estimated cost in USD for this podcast generation
        news_fetch_ms: Time taken to fetch news articles (ms)
        script_generation_ms: Time taken to generate script (ms)
        audio_generation_ms: Time taken to generate audio (ms)
        created_at: Timestamp when metrics were recorded
    """

    __tablename__ = "metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True,
    )

    podcast_id = Column(
        UUID(as_uuid=True),
        ForeignKey("podcasts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    tokens_used = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of tokens consumed by GPT-4o",
    )

    elevenlabs_characters = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of characters processed by ElevenLabs TTS",
    )

    latency_ms = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total end-to-end latency in milliseconds",
    )

    cost_estimate = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Estimated cost in USD for this podcast generation",
    )

    news_fetch_ms = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Time taken to fetch news articles in milliseconds",
    )

    script_generation_ms = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Time taken to generate script in milliseconds",
    )

    audio_generation_ms = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Time taken to generate audio in milliseconds",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Relationships
    podcast = relationship(
        "Podcast",
        back_populates="metrics",
        lazy="selectin",
    )

    # Constraints to ensure data integrity
    __table_args__ = (
        CheckConstraint("tokens_used >= 0", name="check_tokens_non_negative"),
        CheckConstraint(
            "elevenlabs_characters >= 0", name="check_characters_non_negative"
        ),
        CheckConstraint("latency_ms >= 0", name="check_latency_non_negative"),
        CheckConstraint("cost_estimate >= 0", name="check_cost_non_negative"),
        Index("ix_metrics_created_at", "created_at"),
        Index("ix_metrics_cost_estimate", "cost_estimate"),
    )

    def __repr__(self) -> str:
        """String representation of Metrics."""
        return (
            f"<Metrics(id={self.id}, podcast_id={self.podcast_id}, "
            f"cost=${self.cost_estimate:.4f})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Metrics to dictionary representation.

        Returns:
            Dict containing metrics data
        """
        return {
            "id": str(self.id),
            "podcast_id": str(self.podcast_id),
            "tokens_used": self.tokens_used,
            "elevenlabs_characters": self.elevenlabs_characters,
            "latency_ms": self.latency_ms,
            "cost_estimate": self.cost_estimate,
            "news_fetch_ms": self.news_fetch_ms,
            "script_generation_ms": self.script_generation_ms,
            "audio_generation_ms": self.audio_generation_ms,
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def calculate_cost(
        tokens_used: int,
        elevenlabs_characters: int,
        gpt4_cost_per_1k_tokens: float = 0.03,
        elevenlabs_cost_per_1k_chars: float = 0.30,
    ) -> float:
        """
        Calculate estimated cost for podcast generation.

        Args:
            tokens_used: Number of GPT-4o tokens used
            elevenlabs_characters: Number of ElevenLabs characters processed
            gpt4_cost_per_1k_tokens: Cost per 1000 tokens for GPT-4o
            elevenlabs_cost_per_1k_chars: Cost per 1000 characters for ElevenLabs

        Returns:
            Estimated cost in USD
        """
        gpt_cost = (tokens_used / 1000) * gpt4_cost_per_1k_tokens
        elevenlabs_cost = (elevenlabs_characters / 1000) * elevenlabs_cost_per_1k_chars
        return round(gpt_cost + elevenlabs_cost, 4)

    def update_cost_estimate(self) -> None:
        """Update cost estimate based on current usage metrics."""
        self.cost_estimate = self.calculate_cost(
            self.tokens_used,
            self.elevenlabs_characters,
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for this podcast generation.

        Returns:
            Dict containing performance metrics
        """
        total_time = (
            (self.news_fetch_ms or 0)
            + (self.script_generation_ms or 0)
            + (self.audio_generation_ms or 0)
        )

        return {
            "total_latency_ms": self.latency_ms,
            "breakdown": {
                "news_fetch_ms": self.news_fetch_ms,
                "script_generation_ms": self.script_generation_ms,
                "audio_generation_ms": self.audio_generation_ms,
            },
            "resources": {
                "tokens_used": self.tokens_used,
                "characters_processed": self.elevenlabs_characters,
            },
            "cost_usd": self.cost_estimate,
            "efficiency": {
                "ms_per_token": (
                    round(self.latency_ms / self.tokens_used, 2)
                    if self.tokens_used > 0
                    else 0
                ),
                "cost_per_minute": (
                    round(self.cost_estimate / (self.latency_ms / 60000), 4)
                    if self.latency_ms > 0
                    else 0
                ),
            },
        }
