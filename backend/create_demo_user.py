#!/usr/bin/env python3
"""
Create a demo user for the Personal Podcast Generator.
Run this once to set up a default user for testing.
"""

import asyncio
from uuid import uuid4
from app.core.database import async_session_factory
from app.models import User


async def create_demo_user():
    """Create a demo user with default preferences."""

    # Fixed UUID for demo user (easy to remember)
    demo_user_id = "00000000-0000-0000-0000-000000000001"

    async with async_session_factory() as session:
        # Check if demo user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.id == demo_user_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Demo user already exists!")
            print(f"   User ID: {demo_user_id}")
            print(f"   Interests: {existing_user.preferences.get('interests', [])}")
            return demo_user_id

        # Create new demo user
        demo_user = User(
            id=demo_user_id,
            preferences={
                "interests": ["Technology", "AI", "Startups"],
                "language": "en",
                "duration_minutes": 10,
                "voice_settings": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                }
            },
            schedule_settings={
                "enabled": False,
                "frequency": "daily",
                "time": "08:00",
                "timezone": "UTC",
                "days_of_week": [1, 2, 3, 4, 5],
            }
        )

        session.add(demo_user)
        await session.commit()

        print(f"✅ Demo user created successfully!")
        print(f"   User ID: {demo_user_id}")
        print(f"   Interests: {demo_user.preferences['interests']}")
        print(f"\n   Use this ID in your API requests!")

        return demo_user_id


if __name__ == "__main__":
    user_id = asyncio.run(create_demo_user())
