"""
User model for storing user preferences and settings.
"""

from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """
    User model for storing user information and preferences.

    Attributes:
        id: Unique user identifier (UUID)
        preferences: User interests, topics, and content preferences (JSONB)
        schedule_settings: Podcast generation schedule configuration (JSONB)
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        podcasts: Relationship to user's podcasts
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True,
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login",
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address",
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )

    preferences = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="User interests, topics, sources, and content preferences",
    )

    schedule_settings = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Schedule configuration for automated podcast generation",
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
        index=True,
    )

    # Relationships
    podcasts = relationship(
        "Podcast",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, created_at={self.created_at})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User to dictionary representation.

        Returns:
            Dict containing user data
        """
        return {
            "id": str(self.id),
            "preferences": self.preferences,
            "schedule_settings": self.schedule_settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def get_default_preferences(cls) -> Dict[str, Any]:
        """
        Get default user preferences structure.

        Returns:
            Dict containing default preferences
        """
        return {
            "interests": [],
            "topics": [],
            "sources": [],
            "language": "en",
            "duration_minutes": 10,
            "voice_settings": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

    @classmethod
    def get_default_schedule_settings(cls) -> Dict[str, Any]:
        """
        Get default schedule settings structure.

        Returns:
            Dict containing default schedule settings
        """
        return {
            "enabled": False,
            "frequency": "daily",
            "time": "08:00",
            "timezone": "UTC",
            "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
        }
