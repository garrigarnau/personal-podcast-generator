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
        firecrawl_searches: Number of Firecrawl search API calls
        firecrawl_scrapes: Number of Firecrawl scrape API calls
        firecrawl_cost: Estimated Firecrawl API cost in USD
        latency_ms: Total latency in milliseconds for podcast generation
        cost_estimate: Estimated total cost in USD (OpenAI + ElevenLabs + Firecrawl)
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

    firecrawl_searches = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of Firecrawl search API calls",
    )

    firecrawl_scrapes = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of Firecrawl scrape API calls",
    )

    firecrawl_cost = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Estimated Firecrawl API cost in USD",
    )

    openai_cost = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Actual OpenAI API cost in USD",
    )

    elevenlabs_cost = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Actual ElevenLabs API cost in USD",
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
        CheckConstraint("firecrawl_searches >= 0", name="check_firecrawl_searches_non_negative"),
        CheckConstraint("firecrawl_scrapes >= 0", name="check_firecrawl_scrapes_non_negative"),
        CheckConstraint("firecrawl_cost >= 0", name="check_firecrawl_cost_non_negative"),
        CheckConstraint("openai_cost >= 0", name="check_openai_cost_non_negative"),
        CheckConstraint("elevenlabs_cost >= 0", name="check_elevenlabs_cost_non_negative"),
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
            "firecrawl_searches": self.firecrawl_searches,
            "firecrawl_scrapes": self.firecrawl_scrapes,
            "firecrawl_cost": self.firecrawl_cost,
            "openai_cost": self.openai_cost,
            "elevenlabs_cost": self.elevenlabs_cost,
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
        firecrawl_searches: int = 0,
        firecrawl_scrapes: int = 0,
        gpt4_cost_per_1k_tokens: float = 0.03,
        elevenlabs_cost_per_1k_chars: float = 0.30,
        firecrawl_search_cost: float = 0.01,
        firecrawl_scrape_cost: float = 0.005,
    ) -> float:
        """
        Calculate estimated cost for podcast generation.

        DEPRECATED: Use individual cost fields (openai_cost, elevenlabs_cost, firecrawl_cost) instead.
        This method is kept for backward compatibility only.

        Args:
            tokens_used: Number of GPT-4o tokens used
            elevenlabs_characters: Number of ElevenLabs characters processed
            firecrawl_searches: Number of Firecrawl search API calls
            firecrawl_scrapes: Number of Firecrawl scrape API calls
            gpt4_cost_per_1k_tokens: Cost per 1000 tokens for GPT-4o
            elevenlabs_cost_per_1k_chars: Cost per 1000 characters for ElevenLabs
            firecrawl_search_cost: Cost per Firecrawl search request
            firecrawl_scrape_cost: Cost per Firecrawl scrape request

        Returns:
            Estimated total cost in USD
        """
        gpt_cost = (tokens_used / 1000) * gpt4_cost_per_1k_tokens
        elevenlabs_cost = (elevenlabs_characters / 1000) * elevenlabs_cost_per_1k_chars
        firecrawl_cost = (firecrawl_searches * firecrawl_search_cost) + (firecrawl_scrapes * firecrawl_scrape_cost)
        return round(gpt_cost + elevenlabs_cost + firecrawl_cost, 4)

    def update_cost_estimate(self) -> None:
        """Update cost estimate based on actual tracked costs."""
        # Use actual tracked costs if available, otherwise fall back to calculation
        if self.openai_cost > 0 or self.elevenlabs_cost > 0 or self.firecrawl_cost > 0:
            self.cost_estimate = round(
                self.openai_cost + self.elevenlabs_cost + self.firecrawl_cost, 4
            )
        else:
            # Fallback for backward compatibility
            self.cost_estimate = self.calculate_cost(
                self.tokens_used,
                self.elevenlabs_characters,
                self.firecrawl_searches,
                self.firecrawl_scrapes,
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
                "firecrawl_searches": self.firecrawl_searches,
                "firecrawl_scrapes": self.firecrawl_scrapes,
            },
            "cost_breakdown_usd": {
                "openai": self.openai_cost if self.openai_cost > 0 else round((self.tokens_used / 1000) * 0.03, 4),
                "elevenlabs": self.elevenlabs_cost if self.elevenlabs_cost > 0 else round((self.elevenlabs_characters / 1000) * 0.30, 4),
                "firecrawl": self.firecrawl_cost,
                "total": self.cost_estimate,
            },
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
