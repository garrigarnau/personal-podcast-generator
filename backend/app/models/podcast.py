"""
Podcast model for storing generated podcast episodes.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, Optional
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PodcastStatus(PyEnum):
    """
    Enumeration of possible podcast generation statuses.

    PENDING: Podcast generation job has been queued
    PROCESSING: Podcast is currently being generated
    COMPLETED: Podcast generation completed successfully
    FAILED: Podcast generation failed
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Podcast(Base):
    """
    Podcast model for storing generated podcast episodes.

    Attributes:
        id: Unique podcast identifier (UUID)
        user_id: Foreign key to users table
        script: Generated podcast script text
        audio_url: URL or path to generated audio file
        status: Current status of podcast generation
        error_message: Error details if status is FAILED
        podcast_metadata: Additional metadata (topics, sources, etc.)
        created_at: Timestamp when podcast was created
        updated_at: Timestamp when podcast was last updated
        user: Relationship to user
        metrics: Relationship to podcast metrics
    """

    __tablename__ = "podcasts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    script = Column(
        Text,
        nullable=True,
        comment="Generated podcast script content",
    )

    audio_url = Column(
        String(1024),
        nullable=True,
        comment="URL or path to generated audio file",
    )

    status = Column(
        Enum(PodcastStatus),
        nullable=False,
        default=PodcastStatus.PENDING,
        index=True,
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error details if generation failed",
    )

    podcast_metadata = Column(
        Text,
        nullable=True,
        comment="Additional metadata in JSON format",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="podcasts",
        lazy="selectin",
    )

    metrics = relationship(
        "Metrics",
        back_populates="podcast",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_podcasts_user_status", "user_id", "status"),
        Index("ix_podcasts_user_created", "user_id", "created_at"),
        Index("ix_podcasts_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of Podcast."""
        return f"<Podcast(id={self.id}, user_id={self.user_id}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Podcast to dictionary representation.

        Returns:
            Dict containing podcast data
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "script": self.script,
            "audio_url": self.audio_url,
            "status": self.status.value,
            "error_message": self.error_message,
            "podcast_metadata": self.podcast_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def is_processing(self) -> bool:
        """Check if podcast is currently being processed."""
        return self.status in [PodcastStatus.PENDING, PodcastStatus.PROCESSING]

    def is_complete(self) -> bool:
        """Check if podcast generation is complete."""
        return self.status == PodcastStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if podcast generation failed."""
        return self.status == PodcastStatus.FAILED

    def mark_processing(self) -> None:
        """Mark podcast as processing."""
        self.status = PodcastStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, audio_url: str) -> None:
        """
        Mark podcast as completed.

        Args:
            audio_url: URL or path to generated audio file
        """
        self.status = PodcastStatus.COMPLETED
        self.audio_url = audio_url
        self.error_message = None
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark podcast as failed.

        Args:
            error_message: Error details
        """
        self.status = PodcastStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
